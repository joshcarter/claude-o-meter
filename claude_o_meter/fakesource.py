"""Offline fake data source — oscillates ``state.snapshot`` so the whole display
can be developed and demoed on the desktop with no network and no cookie.

Split into a pure ``fake_values(elapsed, now)`` (no clock, no state mutation) and
a thin ``fake_loop`` that applies it on a fast tick. Keeping the math pure lets a
test sweep a full set of cycles and confirm every widget is exercised — the tach
and fuel gauge sweep their full range, both warning lights toggle, the money/
reset readouts move, and each fault message is shown in turn (TD-3.9).
"""

import asyncio
import math
import time

from . import faults, state

CYCLE_SECONDS = 300      # full oscillation period — a 5-minute sweep per gauge
TICK_SECONDS = 0.2       # snapshot refresh — fast enough for smooth animation

# Causes the demo rotates through, one per cycle, during the fault window so the
# check-engine light and each bottom message are seen offline. ``None`` is the
# never-polled "No Data" state (error stays None, last_update 0).
_FAULTS = (None, faults.ERR_AUTH, faults.ERR_CONNECTION, faults.ERR_STALE)

# Fraction of each cycle (at the end) spent faulted: the light blinks on as the
# gauges crest, then clears as they sweep back down.
_FAULT_FROM = 0.8


def fake_values(elapsed, now):
    """Pure: the snapshot field values for ``elapsed`` seconds since start, using
    ``now`` as the wall clock for reset/last-update timestamps. Returns a dict of
    Snapshot field → value.

    Over one cycle the 5-hour burn sweeps the tach 0→redline, the 7-day window
    sweeps the fuel gauge full→near-empty (crossing the 80% low-fuel threshold),
    and the money fields oscillate. The final ``1 − _FAULT_FROM`` of each cycle is
    a fault; successive cycles rotate ``_FAULTS`` so every message is shown.
    """
    phase = (elapsed % CYCLE_SECONDS) / CYCLE_SECONDS              # 0..1
    cycle = int(elapsed // CYCLE_SECONDS)

    five_pct = 40.0 + 40.0 * math.sin(2 * math.pi * phase)            # 0..80
    seven_pct = 50.0 + 45.0 * math.sin(2 * math.pi * phase + 1.0)     # 5..95

    five_hours_remaining = 4.0
    seven_days_remaining = 5.0 * 24.0
    five_sustainable = max((100.0 - five_pct) / five_hours_remaining, 0.001)
    five_burn = five_pct * 0.2
    seven_sustainable = max((100.0 - seven_pct) / seven_days_remaining, 0.001)
    seven_burn = seven_pct * 0.01

    extra_used = 5.0 + 5.0 * math.sin(2 * math.pi * phase + 2.0)      # $0–$10

    values = {
        "five_hour_pct": five_pct,
        "five_hour_resets_at": now + int(five_hours_remaining * 3600),
        "five_hour_burn_rate": five_burn,
        "five_hour_sustainable_rate": five_sustainable,
        "five_hour_redline_ratio": min(five_burn / five_sustainable, 10.0),
        "seven_day_pct": seven_pct,
        "seven_day_resets_at": now + int(seven_days_remaining * 3600),
        "seven_day_burn_rate": seven_burn,
        "seven_day_sustainable_rate": seven_sustainable,
        "seven_day_redline_ratio": min(seven_burn / seven_sustainable, 10.0),
        "extra_usage_used": round(extra_used, 2),
        "extra_usage_limit": 20.0,
        "extra_usage_enabled": True,
        "balance": round(100.0 + 20.0 * math.sin(2 * math.pi * phase + 0.5), 2),
    }

    if phase < _FAULT_FROM:                  # healthy: gauges + money readouts
        values["error"] = None
        values["last_update"] = now
    else:                                    # fault window: light check-engine
        cause = _FAULTS[cycle % len(_FAULTS)]
        values["error"] = cause
        # None cause = never-polled "No Data"; a string = an active error.
        values["last_update"] = 0 if cause is None else now
    return values


async def fake_loop(tick_seconds: float = TICK_SECONDS) -> None:
    """Apply ``fake_values`` to ``state.snapshot`` on a fast tick (no network, no
    Store). ``tick_seconds`` is independent of the live poll cadence so the
    desktop demo animates smoothly rather than stepping once per poll."""
    t0 = time.time()
    while True:
        now = int(time.time())
        for field, value in fake_values(time.time() - t0, now).items():
            setattr(state.snapshot, field, value)
        await asyncio.sleep(tick_seconds)
