# Done

Completed TD trees, most recent first.

## 2026-06-01 refinement

- [x] TD-12 Capture & expose the extra-usage and balance feeds on the snapshot
  The display needs three money readouts the current poller discards. `extra_usage`
  is already in the `/usage` response (`used_credits`, `monthly_limit`, both cents);
  balance comes from a **second** call, `GET /api/organizations/{org}/prepaid/credits`
  → `amount` (cents). Normalize cents→USD at the poller boundary so the display
  never sees cents. Confirmed units: `monthly_limit` 2000=$20, balance 12000=$120.
  All slow-changing → snapshot-only (no `store` history, unlike 5h/7d). Defensive:
  null / 404 / non-USD / Cloudflare hiccup on these must NOT set `stale` or
  `auth_failed`.
  - [x] TD-12.1 Parse `extra_usage` from the existing `/usage` response in
        `poller.py`: `used_credits`, `monthly_limit`, `is_enabled`. Store as USD
        floats (÷100) on `state.Snapshot`. `used_credits` unit is unverified
        (was 0.0) — assume cents but log the raw value on first nonzero to confirm.
  - [x] TD-12.2 Add a second upstream fetch to `/api/organizations/{org}/prepaid/credits`
        on a **slow cadence** (every N usage-polls / few minutes). Extract `amount`
        (÷100 → USD) to the snapshot. Tolerate 404/null without affecting freshness.
  - [x] TD-12.3 Currency guard: if any of these reports `currency != "USD"`, treat
        that value as `None` (unavailable) and log once. Multi-currency is TD-13.
  - [x] TD-12.4 Add the new fields to `state.Snapshot` (extra-usage used, extra-usage
        limit, balance — USD floats or null) and a unit test on the cents→USD
        parsing. (No `api.py`/`/status` to update — display reads the snapshot
        directly.)
  - [x] TD-12.5 Make the `fake` data source (TD-1.3) emit the new money fields too,
        so the display can be developed against it without a live cookie.

- [x] TD-1 Stand up the single `claude-o-meter` app skeleton on the Mac (poll loop in-process)
  One program does both polling and display. This TD wires up the polling half
  and proves it runs locally — no Pi, no systemd, no HTTP. Reuse the existing
  `server/src/` logic (`polling_loop`, `state.snapshot`, `Store`) as a library;
  do not re-implement it. `impersonate="chrome124"` in `poller.py` (Cloudflare TLS
  fingerprinting on claude.ai) is why curl_cffi is required — keep it. On macOS
  the curl_cffi wheel installs cleanly; the aarch64-wheel concern is a Pi issue
  (TD-4), not here.
  - [x] TD-1.1 Scaffold the `claude_o_meter/` package: `main.py` (entrypoint),
        `config.toml` (DATA_SOURCE, POLL_SECONDS, UTC_OFFSET_HOURS, dim opacity,
        window vs framebuffer), `requirements.txt` (pygame, curl_cffi). Relocate /
        import `poller.py`, `state.py`, `store.py` from `server/src/` as the
        polling library (no logic changes).
  - [x] TD-1.2 Run `polling_loop` on a **background thread** with its own asyncio
        loop, writing the module-global `state.snapshot`. The main thread owns
        pygame later; for now have it read `state.snapshot` and log it once a
        second to prove the shared-state hand-off works.
  - [x] TD-1.3 Add a **data-source selector** in `config.toml`: `live` (curl_cffi
        + `CLAUDE_SESSION_KEY`) vs `fake` (oscillating demo values, no network, no
        cookie) so the whole app runs offline on any desktop. The fake source
        populates the same `Snapshot` fields the live poller does.
  - [x] TD-1.4 Verify on the Mac: `python -m claude_o_meter` starts, the poll
        thread fills the snapshot. With `fake` the 5h/7d values oscillate; with
        `live` + a real cookie, `snapshot.stale` flips to `false` after one
        interval. (Replaces the old "curl /status" check — there is no HTTP now.)
