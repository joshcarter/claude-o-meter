# TODO — Critical

Core path to a working **claude-o-meter** dashboard. Develop desktop-first, then
deploy the same program to the Pi 3. Rough dependency order:
TD-1 (single app skeleton polling in-process on the Mac) → TD-12 (capture the new
money feeds into the snapshot) → TD-2 (assets) → TD-3 (pygame instrument cluster
in a 480×320 window) → TD-4 (Pi 3 + PiTFT deployment, one systemd service).

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

- [ ] TD-12 Capture & expose the extra-usage and balance feeds on the snapshot
  The display needs three money readouts the current poller discards. `extra_usage`
  is already in the `/usage` response (`used_credits`, `monthly_limit`, both cents);
  balance comes from a **second** call, `GET /api/organizations/{org}/prepaid/credits`
  → `amount` (cents). Normalize cents→USD at the poller boundary so the display
  never sees cents. Confirmed units: `monthly_limit` 2000=$20, balance 12000=$120.
  All slow-changing → snapshot-only (no `store` history, unlike 5h/7d). Defensive:
  null / 404 / non-USD / Cloudflare hiccup on these must NOT set `stale` or
  `auth_failed`.
  - [ ] TD-12.1 Parse `extra_usage` from the existing `/usage` response in
        `poller.py`: `used_credits`, `monthly_limit`, `is_enabled`. Store as USD
        floats (÷100) on `state.Snapshot`. `used_credits` unit is unverified
        (was 0.0) — assume cents but log the raw value on first nonzero to confirm.
  - [ ] TD-12.2 Add a second upstream fetch to `/api/organizations/{org}/prepaid/credits`
        on a **slow cadence** (every N usage-polls / few minutes). Extract `amount`
        (÷100 → USD) to the snapshot. Tolerate 404/null without affecting freshness.
  - [ ] TD-12.3 Currency guard: if any of these reports `currency != "USD"`, treat
        that value as `None` (unavailable) and log once. Multi-currency is TD-13.
  - [ ] TD-12.4 Add the new fields to `state.Snapshot` (extra-usage used, extra-usage
        limit, balance — USD floats or null) and a unit test on the cents→USD
        parsing. (No `api.py`/`/status` to update — display reads the snapshot
        directly.)
  - [ ] TD-12.5 Make the `fake` data source (TD-1.3) emit the new money fields too,
        so the display can be developed against it without a live cookie.

- [ ] TD-2 Prepare display assets for the dimming-rectangle render model
  New model: **one "all-segments-lit" bitmap per instrument**, darkened by dim
  rectangles. Drops the old 21-frame PNG export entirely. Art source =
  `graphics/*.afdesign`; fonts named in `pyportal/README.md`. Exact pixel
  dimensions / segment-boundary coordinates pending (see TODO.md "Pending input").
  - [ ] TD-2.1 Export one full-on bitmap for the **horizontal 20-segment tach bar**
        (blue/yellow/red bands as today) into `claude_o_meter/assets/`.
  - [ ] TD-2.2 Export one full-on bitmap for the **vertical 20-segment fuel gauge**.
  - [ ] TD-2.3 Export the **warning lights** in their lit state — "low fuel" and
        "check engine" — to be dimmed-when-off via the same overlay mechanism.
  - [ ] TD-2.4 Place the two fonts as TTF/OTF in `claude_o_meter/assets/fonts/`
        (DESG7Modern-Italic for the 0–99 readout + dollar amounts; Dogica-Pixel
        for labels / messages / reset times). Sizes pending pixel spec. Drop the
        `otf2bdf` step.

- [ ] TD-3 Build the pygame display half (`claude_o_meter/`) — the full instrument cluster
  Port pure logic verbatim; delete all ESP32/WiFi code. Runs in the same process
  as the TD-1 poll thread and reads `state.snapshot` directly (no `requests`, no
  HTTP). Develop on the Mac in a **windowed 480×320 SDL surface** against the
  `fake` data source. Use named layout constants so the pending pixel/font spec
  can drop in later without restructuring.
  - [ ] TD-3.1 Add `render.py` and `layout.py` (pixel constants + segment
        boundaries) to the package. `main.py` opens a 480×320 window and runs the
        pygame loop on the main thread, reading the shared `state.snapshot` each
        frame.
  - [ ] TD-3.2 Port pure helpers verbatim from `code.py`: `tach_position()`,
        `fmt_hhmm()`, `fmt_duration()`, `_clamp01()`. Tach keeps the `redline_ratio`
        mapping and knobs (`REDLINE_FRAME`, `BLUE_EXPONENT`, `RED_FULL_RATIO`).
  - [ ] TD-3.3 Dimming primitive: a reusable "reveal N of M segments" helper that
        blits a full-on bitmap then a black `SRCALPHA` rectangle whose edge **snaps
        to a segment boundary**. Right-pinned (horizontal) and top-pinned (vertical)
        variants. Opacity tunable, default alpha≈212 (~83%, matches current ghost).
  - [ ] TD-3.4 Horizontal tach bar + 0–99 readout: segment count and number both
        driven by `redline_ratio` via `tach_position()` (mirrors `update_tach`).
        Number = DESG7 font, dark "88" ghost + live value overlay.
  - [ ] TD-3.5 Vertical fuel gauge: `fuel = clamp(100 − seven_day.utilization, 0,
        100)`, quantized to 20 segments, draining top→bottom (top-pinned dim).
  - [ ] TD-3.6 Low-fuel light: lit when remaining ≤ 20% (`utilization ≥ 80`),
        else dimmed.
  - [ ] TD-3.7 Money + reset readouts: extra-use $, extra-limit $, balance $ (USD
        from the snapshot; format `$X.XX`, clamp ≥999.99 defensively); 7-day reset
        date; 5-hour reset time (`fmt_hhmm`). USD only.
  - [ ] TD-3.8 Fault state machine reading the snapshot: map
        poll-failure / data-stale (`snapshot.stale`) / needs-auth
        (`snapshot.auth_failed`) → check-engine light + a distinct message each;
        billing-feed failures excluded. **Delete** `wifi_kickoff`/`wifi_finish`/
        `wifi_recover` and all ESP32 reset logic — there is no network layer in the
        display half anymore.
  - [ ] TD-3.9 Verify on the Mac (windowed 480×320, `fake` source): tach, fuel
        gauge, both lights, money/reset readouts, and the check-engine fault
        overlay all animate through the fake source's cycles. This is the
        desktop-supported run target, not just a test.

- [ ] TD-4 Pi 3 + PiTFT 480×320 deployment — one systemd service
  The same program, now on hardware. The fiddly phase. SDL2 dropped fbcon, so
  mirror the framebuffer onto the panel. Only **one** service: `claude-o-meter`.
  - [ ] TD-4.1 Flash **64-bit Raspberry Pi OS Bullseye** on the Pi 3; enable SSH +
        WiFi. Bullseye-64 gets both the aarch64 curl_cffi wheel (glibc ≥2.28) and
        Adafruit PiTFT installer support. Create a venv,
        `pip install -r claude_o_meter/requirements.txt`; confirm `curl-cffi`
        installs from a **prebuilt aarch64 wheel** (compiler output = wrong
        arch/OS). Pin `curl-cffi>=0.15`.
  - [ ] TD-4.2 Run Adafruit's `adafruit-pitft.py` installer; confirm the panel
        appears as `/dev/fb1`. Install `fbcp-ili9341` to mirror `fb0` → the TFT at
        480×320.
  - [ ] TD-4.3 Switch `claude_o_meter` from a window to the framebuffer (SDL
        `kmsdrm`/`dummy` against `fb0`, selected via `config.toml`); confirm the
        full cluster renders on the physical panel with the `live` data source.
  - [ ] TD-4.4 Write `deploy/claude-o-meter.service` (one unit): `ExecStart`=
        `<venv>/bin/python -m claude_o_meter`, `EnvironmentFile`=`.env`
        (`CLAUDE_SESSION_KEY`), `DB_PATH=/var/lib/claude-o-meter/samples.db`,
        `Restart=always`. Reboot and confirm the dashboard comes up unattended.
        (Replaces Docker and the old two-service split.)
