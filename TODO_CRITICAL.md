# TODO — Critical

Core path to a working all-in-one Pi 3 dashboard. Rough dependency order:
TD-1 (server up) → TD-12 (capture new feeds) → TD-2 (assets) → TD-3 (display
client, dev on Mac) → TD-4 (PiTFT bring-up + boot services).

- [ ] TD-1 Stand up the existing poller on the Pi 3 under systemd
  Server code is already Linux-native (`server/src/`), no logic changes for this
  TD. The one real risk is the `curl_cffi` native wheel — it exists for `aarch64`
  but the install must NOT fall back to a source build. `impersonate="chrome124"`
  at `server/src/poller.py:115` is why curl_cffi is required (Cloudflare TLS
  fingerprinting on claude.ai); do not drop it.
  - [ ] TD-1.1 Flash **64-bit Raspberry Pi OS Bullseye** on the Pi 3; enable SSH + WiFi.
        Bullseye-64 gets both the aarch64 curl_cffi wheel (glibc ≥2.28) and
        Adafruit PiTFT installer support (TD-4.1). Bookworm KMS is fiddlier.
  - [ ] TD-1.2 Create a venv, `pip install -r server/requirements.txt`; confirm
        `curl-cffi` installs from a prebuilt aarch64 wheel (watch for compiler
        output → wrong arch/OS). Bump the pin to `curl-cffi>=0.15`.
  - [ ] TD-1.3 Write `deploy/claude-poller.service`: `WorkingDirectory`=`server/`,
        `ExecStart=<venv>/bin/python -m src.main`, `EnvironmentFile`=`.env`
        (`CLAUDE_SESSION_KEY`), `DB_PATH=/var/lib/claude_portal/samples.db`,
        `Restart=always`. (Replaces Docker.)
  - [ ] TD-1.4 Verify: `curl http://localhost:7654/status` returns `"stale": false`
        with live percentages after one poll interval.

- [ ] TD-12 Extend the server to capture & expose the extra-usage and balance feeds
  The display needs three money readouts the current server discards. `extra_usage`
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
  - [ ] TD-12.4 Expose the new fields in `/status` (`api.py`) — extra-usage used,
        extra-usage limit, balance (USD floats or null). Update `test_api_shape.py`.
  - [ ] TD-12.5 Update `mock_server/mock_server.py` to emit the new fields so the
        display can be developed against it without a live cookie.

- [ ] TD-2 Prepare display assets for the dimming-rectangle render model
  New model: **one "all-segments-lit" bitmap per instrument**, darkened by dim
  rectangles. Drops the old 21-frame PNG export entirely. Art source =
  `graphics/*.afdesign`; fonts named in `pyportal/README.md`. Exact pixel
  dimensions / segment-boundary coordinates pending (see TODO.md "Pending input").
  - [ ] TD-2.1 Export one full-on bitmap for the **horizontal 20-segment tach bar**
        (blue/yellow/red bands as today) into `display/assets/`.
  - [ ] TD-2.2 Export one full-on bitmap for the **vertical 20-segment fuel gauge**.
  - [ ] TD-2.3 Export the **warning lights** in their lit state — "low fuel" and
        "check engine" — to be dimmed-when-off via the same overlay mechanism.
  - [ ] TD-2.4 Place the two fonts as TTF/OTF in `display/assets/fonts/`
        (DESG7Modern-Italic for the 0–99 readout + dollar amounts; Dogica-Pixel
        for labels / messages / reset times). Sizes pending pixel spec. Drop the
        `otf2bdf` step.

- [ ] TD-3 Build the pygame display client (`display/`) — the full instrument cluster
  Port pure logic verbatim; delete all ESP32/WiFi code. Develop on the Mac first
  (windowed SDL) against `mock_server.py`. Use named layout constants so the
  pending pixel/font spec can drop in later without restructuring.
  - [ ] TD-3.1 Scaffold `display/`: `main.py`, `render.py`, `layout.py` (pixel
        constants + segment boundaries), `config.toml` (SERVER_URL, POLL_SECONDS,
        UTC_OFFSET_HOURS, dim opacity), `requirements.txt` (pygame, requests).
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
        from server; format `$X.XX`, clamp ≥999.99 defensively); 7-day reset date;
        5-hour reset time (`fmt_hhmm`). USD only.
  - [ ] TD-3.8 `main.py` poll loop + fault state machine: map
        poller-unreachable / data-stale / needs-auth → check-engine light + a
        distinct message each; billing-feed failures excluded. Port the `show_*`
        ladder using `requests`; **delete** `wifi_kickoff`/`wifi_finish`/
        `wifi_recover` and all ESP32 reset logic.
  - [ ] TD-3.9 Verify on the Mac against `mock_server.py` (windowed SDL): tach,
        fuel gauge, both lights, money/reset readouts, and the check-engine fault
        overlay all animate through the mock's cycles.

- [ ] TD-4 PiTFT 480×320 bring-up and boot services
  The fiddly phase. SDL2 dropped fbcon, so mirror the framebuffer onto the panel.
  - [ ] TD-4.1 Run Adafruit's `adafruit-pitft.py` installer; confirm the panel
        appears as `/dev/fb1`. (OS chosen as Bullseye-64 in TD-1.1.)
  - [ ] TD-4.2 Install `fbcp-ili9341` to mirror `fb0` → the TFT; set 480×320 mode.
  - [ ] TD-4.3 Point pygame at the framebuffer (SDL `kmsdrm`/`dummy` against `fb0`);
        confirm `display/main.py` renders on the physical panel.
  - [ ] TD-4.4 Write `deploy/claude-display.service`: start `display/main.py` on
        boot, `Restart=always`. Reboot and confirm the dashboard comes up unattended.
