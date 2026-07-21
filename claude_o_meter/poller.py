import asyncio
import logging
import os
import time
from typing import Optional

from curl_cffi.requests import AsyncSession

from . import faults
from .store import Store

log = logging.getLogger(__name__)

CLAUDE_BASE = "https://claude.ai"
STALE_AFTER = 300  # 5 minutes
SEVEN_DAY_BURN_BASELINE = 3 * 3600  # 7d utilization moves slowly; a 30-min delta is just noise
FIVE_HOUR_BURN_WINDOW = 30 * 60  # regression window for the 5h burn rate
FIVE_HOUR_BURN_MIN_SPAN = 10 / 60  # hours of spread required before a slope is trusted
# Window lengths implied by the API's resets_at (rolling session windows).
FIVE_HOUR_WINDOW_HOURS = 5.0
SEVEN_DAY_WINDOW_HOURS = 7 * 24.0
# When the regression has too little history, fall back to utilization /
# hours-elapsed-in-window. Guard elapsed so a 1-minute-old window with a few
# percent used doesn't peg the tach at hundreds of %/hr.
FIVE_HOUR_AVG_MIN_ELAPSED = 5 / 60   # 5 minutes into the 5h window
SEVEN_DAY_AVG_MIN_ELAPSED = 30 / 60  # 30 minutes into the 7d window
SEVEN_DAY_BURN_MIN_SPAN = 1.0        # hours of spread required for 7d regression
MAX_REDLINE_RATIO = 10.0
BALANCE_POLL_EVERY = 5  # fetch balance every N usage polls
PRUNE_EVERY = 60  # prune aged rows ~hourly at the default 60s cadence (see below)

_extra_usage_nonzero_logged = False
_currency_warned: set[str] = set()


def _session_key() -> str:
    val = os.environ.get("CLAUDE_SESSION_KEY", "")
    if not val:
        raise RuntimeError("CLAUDE_SESSION_KEY is not set")
    return val


def _poll_interval() -> int:
    return int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))


def _parse_cents_usd(raw) -> Optional[float]:
    """Convert a cents value (int or float) to USD. Returns None if raw is None."""
    if raw is None:
        return None
    return float(raw) / 100.0


def _currency_ok(value: Optional[str], label: str) -> bool:
    """Return True if currency is USD or absent. Log once per unexpected currency."""
    if value is None or value == "USD":
        return True
    if value not in _currency_warned:
        _currency_warned.add(value)
        log.warning("%s: currency %r is not USD — value treated as unavailable (TD-13)", label, value)
    return False


async def _fetch_org_id(session: AsyncSession) -> Optional[str]:
    pinned = os.environ.get("CLAUDE_ORG_ID")
    if pinned:
        return pinned
    resp = await session.get(
        f"{CLAUDE_BASE}/api/organizations",
        cookies={"sessionKey": _session_key()},
        timeout=15,
    )
    resp.raise_for_status()
    orgs = resp.json()
    if not orgs:
        raise ValueError("No organizations returned")
    return orgs[0]["uuid"]


async def _fetch_balance(session: AsyncSession, org_id: str) -> Optional[float]:
    """Fetch prepaid credit balance. Returns USD float or None. Raises on transient errors."""
    resp = await session.get(
        f"{CLAUDE_BASE}/api/organizations/{org_id}/prepaid/credits",
        cookies={"sessionKey": _session_key()},
        timeout=15,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return None
    if not _currency_ok(data.get("currency"), "balance"):
        return None
    return _parse_cents_usd(data.get("amount"))


def _burn_rate(rows: list[tuple[int, float]], min_dt_hours: float) -> Optional[float]:
    """Least-squares burn rate (pct/hour) across the sample window.

    Returns ``None`` when there isn't enough history to compute a slope (fewer
    than two samples, or a span shorter than ``min_dt_hours``) — distinct from
    ``0.0``, which means a real flat or decaying burn. The caller surfaces the
    ``None`` case as a "collecting data" warm-up state rather than a zero gauge,
    unless a window-average provisional rate is available.

    Uses every sample, not just the endpoints, so integer-quantized utilization
    readings average out instead of jolting the slope as steps age in and out.
    """
    if len(rows) < 2:
        return None

    if (rows[-1][0] - rows[0][0]) / 3600 < min_dt_hours:
        return None

    n = len(rows)
    t0 = rows[0][0]
    ts = [(ts - t0) / 3600 for ts, _ in rows]
    ys = [pct for _, pct in rows]
    mean_t = sum(ts) / n
    mean_y = sum(ys) / n
    var_t = sum((t - mean_t) ** 2 for t in ts)
    if var_t == 0:
        return None

    cov = sum((t - mean_t) * (y - mean_y) for t, y in zip(ts, ys))
    rate = cov / var_t
    return rate if rate > 0 else 0.0


def _window_average_burn(
    pct: float,
    resets_at: Optional[int],
    window_hours: float,
    now: int,
    min_elapsed_hours: float,
) -> Optional[float]:
    """Provisional burn rate: utilization / hours elapsed in the current window.

    Available from a single poll once the window has been open long enough to
    be meaningful. Coarser than the sample regression (it is the average pace
    since the window opened, not the recent slope) but far better than a blank
    gauge while samples accumulate.
    """
    if resets_at is None:
        return None
    hours_to_reset = (resets_at - now) / 3600
    if hours_to_reset <= 0:
        return None
    hours_elapsed = window_hours - hours_to_reset
    if hours_elapsed < min_elapsed_hours:
        return None
    # Clock skew / API quirks: never treat elapsed as larger than the window.
    if hours_elapsed > window_hours:
        hours_elapsed = window_hours
    rate = pct / hours_elapsed
    return rate if rate > 0 else 0.0


def _sample_since(
    now: int, lookback_seconds: int, resets_at: Optional[int], window_hours: float
) -> int:
    """Earliest timestamp to include in a burn regression.

    Clips the lookback to the current window start (``resets_at − window``) so
    pre-reset samples — which jump from high util to ~0 — cannot drag the slope
    negative and report a false idle right after a reset.
    """
    since = now - lookback_seconds
    if resets_at is not None:
        window_start = resets_at - int(window_hours * 3600)
        if window_start > since:
            since = window_start
    return since


def _compute_five_hour_burn(
    store: Store,
    pct: Optional[float] = None,
    resets_at: Optional[int] = None,
    now: Optional[int] = None,
) -> Optional[float]:
    """5h burn rate: prefer recent regression; fall back to window average.

    ``pct`` / ``resets_at`` / ``now`` enable the provisional average-since-window-
    open estimate when there is not yet enough sample span for a trusted slope.
    Omitting them keeps the pure-regression behaviour (used by older tests).
    """
    if now is None:
        now = int(time.time())
    since = _sample_since(now, FIVE_HOUR_BURN_WINDOW, resets_at, FIVE_HOUR_WINDOW_HOURS)
    rate = _burn_rate(store.recent_five_hour(since), FIVE_HOUR_BURN_MIN_SPAN)
    if rate is not None:
        return rate
    if pct is None:
        return None
    return _window_average_burn(
        pct, resets_at, FIVE_HOUR_WINDOW_HOURS, now, FIVE_HOUR_AVG_MIN_ELAPSED
    )


def _compute_seven_day_burn(
    store: Store,
    pct: Optional[float] = None,
    resets_at: Optional[int] = None,
    now: Optional[int] = None,
) -> Optional[float]:
    """7d burn rate: prefer multi-hour regression; fall back to window average."""
    if now is None:
        now = int(time.time())
    since = _sample_since(
        now, SEVEN_DAY_BURN_BASELINE, resets_at, SEVEN_DAY_WINDOW_HOURS
    )
    rate = _burn_rate(store.recent_seven_day(since), SEVEN_DAY_BURN_MIN_SPAN)
    if rate is not None:
        return rate
    if pct is None:
        return None
    return _window_average_burn(
        pct, resets_at, SEVEN_DAY_WINDOW_HOURS, now, SEVEN_DAY_AVG_MIN_ELAPSED
    )


def _compute_fable_burn(store: Store) -> Optional[float]:
    # Fable is a weekly window like seven_day, so it uses the same slow-moving
    # baseline and 1-hour minimum span before a slope is trusted.
    return _burn_rate(store.recent_fable(int(time.time()) - SEVEN_DAY_BURN_BASELINE), 1.0)


def _extract_fable(data: dict) -> tuple[Optional[float], Optional[str]]:
    """Pull the Fable window's (utilization %, resets_at) from the usage payload.

    Fable is no longer a top-level ``seven_day_*`` field; it arrives in the
    ``limits[]`` array as the model-scoped weekly entry whose
    ``scope.model.display_name`` is ``"Fable"``. Returns ``(None, None)`` when no
    such entry is present (older payload shape, or Fable not surfaced for this
    account) so the gauge reads empty rather than crashing.
    """
    for entry in data.get("limits") or ():
        scope = entry.get("scope") or {}
        model = scope.get("model") or {}
        if model.get("display_name") == "Fable":
            pct = entry.get("percent")
            return (float(pct) if pct is not None else None), entry.get("resets_at")
    return None, None


def _fmt_ratio(ratio: Optional[float]) -> str:
    return "n/a" if ratio is None else "{:.2f}".format(ratio)


def _redline(
    pct: float, resets_at: Optional[int], burn: Optional[float], now: int
) -> tuple[Optional[float], Optional[float]]:
    """Return (sustainable pct/hour, redline_ratio) for a usage window; ratio 1.0 = redline.

    ``burn is None`` (not enough history) propagates to a ``None`` ratio — the
    gauge reads "unknown / warming up", not zero.
    """
    if resets_at is None:
        return None, None
    hours_to_reset = (resets_at - now) / 3600
    if hours_to_reset <= 0:
        return None, None

    sustainable = max(0.0, (100.0 - pct) / hours_to_reset)
    if burn is None:
        return sustainable, None
    if burn <= 0:
        return sustainable, 0.0
    if sustainable <= 0:
        return sustainable, MAX_REDLINE_RATIO
    return sustainable, min(burn / sustainable, MAX_REDLINE_RATIO)


def _mark_stale_if_aged(snapshot, now: int) -> None:
    """Age data we once had into a stale fault. Runs at the top of every poll
    iteration so it fires even on paths that ``continue`` (e.g. a run of 429s).
    Skips when a more specific cause is already set, and before the first
    successful poll (``last_update == 0``, which reads as "No Data")."""
    if (
        snapshot.error is None
        and snapshot.last_update
        and now - snapshot.last_update > STALE_AFTER
    ):
        snapshot.error = faults.ERR_STALE


async def polling_loop(store: Store) -> None:
    from . import state

    global _extra_usage_nonzero_logged

    interval = _poll_interval()
    backoff = interval
    auth_incident_notified = False
    # Start "due" so the balance is fetched on the first successful poll (not
    # ~5 polls / minutes later, which would show $0.00 at startup); the every-N
    # slow cadence applies to subsequent fetches.
    balance_poll_counter = BALANCE_POLL_EVERY
    prune_counter = 0

    async with AsyncSession(impersonate="chrome124") as session:
        while True:
            # Age-out check runs first so every path (including the 429/auth
            # continues below) gets a chance to mark data stale.
            _mark_stale_if_aged(state.snapshot, int(time.time()))

            # Re-checked every iteration: the key can be exported into the
            # environment while the poller is already running.
            if not os.environ.get("CLAUDE_SESSION_KEY"):
                state.snapshot.error = faults.ERR_NO_TOKEN
                await asyncio.sleep(interval)
                continue

            try:
                if state.org_id is None:
                    state.org_id = await _fetch_org_id(session)
                    log.info("Discovered org_id: %s", state.org_id)

                resp = await session.get(
                    f"{CLAUDE_BASE}/api/organizations/{state.org_id}/usage",
                    cookies={"sessionKey": _session_key()},
                    timeout=15,
                )

                if resp.status_code not in (200, 429):
                    log.warning("HTTP %s — body: %.500s", resp.status_code, resp.text)

                if resp.status_code in (401, 403):
                    log.warning("Auth failure (%s) — %s", resp.status_code, faults.ERR_AUTH)
                    state.snapshot.error = faults.ERR_AUTH
                    if not auth_incident_notified:
                        auth_incident_notified = True
                        log.error("Cookie needs renewal — update CLAUDE_SESSION_KEY and restart")
                    backoff = min(backoff * 2, 300)
                    await asyncio.sleep(backoff)
                    continue

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", "60"))
                    retry_after = min(retry_after, 300)
                    log.warning("Rate limited, retrying in %ds", retry_after)
                    await asyncio.sleep(retry_after)
                    continue

                resp.raise_for_status()

                try:
                    data = resp.json()
                    fh = data["five_hour"]
                    sd = data["seven_day"]
                    sdo = data.get("seven_day_opus")

                    now = int(time.time())
                    five_pct = float(fh["utilization"])
                    seven_pct = float(sd["utilization"])
                    opus_pct = float(sdo["utilization"]) if sdo else None
                    fable_pct, fable_resets_raw = _extract_fable(data)

                    store.insert(now, five_pct, seven_pct, opus_pct, fable_pct)
                    # Prune is a DELETE — a write — and running it every poll is
                    # needless SD-card churn. Batching to ~hourly drops ~98% of
                    # the delete traffic; the table just carries up to PRUNE_EVERY
                    # rows past the 7-day cap in between (a few KB, harmless).
                    prune_counter += 1
                    if prune_counter >= PRUNE_EVERY:
                        prune_counter = 0
                        store.prune(now - 7 * 24 * 3600)

                    five_resets = _iso_to_unix(fh["resets_at"])
                    seven_resets = _iso_to_unix(sd["resets_at"])

                    five_burn = _compute_five_hour_burn(
                        store, five_pct, five_resets, now
                    )
                    five_sustainable, five_ratio = _redline(
                        five_pct, five_resets, five_burn, now
                    )
                    seven_burn = _compute_seven_day_burn(
                        store, seven_pct, seven_resets, now
                    )
                    seven_sustainable, seven_ratio = _redline(
                        seven_pct, seven_resets, seven_burn, now
                    )
                    fable_resets = _iso_to_unix(fable_resets_raw)
                    fable_burn = _compute_fable_burn(store)
                    fable_sustainable, fable_ratio = _redline(
                        fable_pct if fable_pct is not None else 0.0,
                        fable_resets, fable_burn, now
                    )

                    state.snapshot.five_hour_pct = five_pct
                    state.snapshot.five_hour_resets_at = five_resets
                    state.snapshot.five_hour_burn_rate = five_burn
                    state.snapshot.five_hour_sustainable_rate = five_sustainable
                    state.snapshot.five_hour_redline_ratio = five_ratio
                    # No 5h burn yet (too few samples) → "collecting data" warm-up.
                    state.snapshot.five_hour_warming_up = five_burn is None
                    state.snapshot.seven_day_pct = seven_pct
                    state.snapshot.seven_day_resets_at = seven_resets
                    state.snapshot.seven_day_burn_rate = seven_burn
                    state.snapshot.seven_day_sustainable_rate = seven_sustainable
                    state.snapshot.seven_day_redline_ratio = seven_ratio
                    state.snapshot.seven_day_opus_pct = opus_pct
                    state.snapshot.seven_day_opus_resets_at = (
                        _iso_to_unix(sdo["resets_at"]) if sdo else None
                    )
                    state.snapshot.fable_pct = fable_pct
                    state.snapshot.fable_resets_at = fable_resets
                    state.snapshot.fable_burn_rate = fable_burn
                    state.snapshot.fable_sustainable_rate = fable_sustainable
                    state.snapshot.fable_redline_ratio = fable_ratio

                    # TD-12.1 + TD-12.3: parse extra_usage from usage response
                    eu = data.get("extra_usage") or {}
                    if _currency_ok(eu.get("currency"), "extra_usage"):
                        raw_used = eu.get("used_credits")
                        if raw_used is not None and float(raw_used) != 0.0 and not _extra_usage_nonzero_logged:
                            log.info("extra_usage.used_credits first nonzero raw: %s (assumed cents)", raw_used)
                            _extra_usage_nonzero_logged = True
                        state.snapshot.extra_usage_used = _parse_cents_usd(raw_used)
                        state.snapshot.extra_usage_limit = _parse_cents_usd(eu.get("monthly_limit"))
                        state.snapshot.extra_usage_enabled = eu.get("is_enabled")
                    else:
                        state.snapshot.extra_usage_used = None
                        state.snapshot.extra_usage_limit = None
                        state.snapshot.extra_usage_enabled = None

                    state.snapshot.error = None
                    state.snapshot.last_update = now
                    auth_incident_notified = False
                    backoff = interval

                    log.debug(
                        "Polled: 5h=%.1f%% redline=%s  7d=%.1f%% redline=%s",
                        five_pct,
                        _fmt_ratio(five_ratio),
                        seven_pct,
                        _fmt_ratio(seven_ratio),
                    )

                    # TD-12.2: slow-cadence balance fetch
                    balance_poll_counter += 1
                    if balance_poll_counter >= BALANCE_POLL_EVERY and state.org_id is not None:
                        balance_poll_counter = 0
                        try:
                            state.snapshot.balance = await _fetch_balance(session, state.org_id)
                        except Exception as exc:
                            log.warning("Balance fetch failed (non-fatal): %s", exc)

                except (KeyError, ValueError, TypeError, AttributeError) as exc:
                    log.error("Unexpected response shape: %s — raw: %.500s", exc, resp.text)
                    state.snapshot.error = faults.ERR_RESPONSE

            except Exception as exc:
                log.warning("Request error: %s", exc)
                state.snapshot.error = faults.ERR_CONNECTION
                backoff = min(backoff + 30, 120)

            await asyncio.sleep(backoff)


def _iso_to_unix(ts: Optional[str]) -> Optional[int]:
    """Parse an API ISO timestamp to unix seconds, or None when the field is null.

    The API reports ``resets_at: null`` for a window with no recent usage — an
    idle 5-hour window at startup, or an unused quota tier. ``_redline`` and the
    reset readouts already treat None as "no reset to show" (blank/ghost), so we
    propagate the null rather than crash. Without this guard the AttributeError
    surfaced as a misleading "Connection Error".
    """
    if ts is None:
        return None
    from datetime import datetime, timezone
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return int(dt.replace(tzinfo=timezone.utc).timestamp()) if dt.tzinfo is None else int(dt.timestamp())
