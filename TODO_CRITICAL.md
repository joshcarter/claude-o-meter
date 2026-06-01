# TODO — Critical

Core path to a working **claude-o-meter** dashboard. Develop desktop-first, then
deploy the same program to the Pi 3. Rough dependency order:
TD-1 (single app skeleton polling in-process on the Mac) → TD-12 (capture the new
money feeds into the snapshot) → TD-2 (assets) → TD-3 (pygame instrument cluster
in a 480×320 window) → TD-4 (Pi 3 + PiTFT deployment, one systemd service).

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
