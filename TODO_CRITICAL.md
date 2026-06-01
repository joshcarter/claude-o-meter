# TODO — Critical

Core path to a working **claude-o-meter** dashboard. Develop desktop-first, then
deploy the same program to the Pi 3. Rough dependency order:
TD-1 (single app skeleton polling in-process on the Mac) → TD-12 (capture the new
money feeds into the snapshot) → TD-2 (assets) → TD-3 (pygame instrument cluster
in a 480×320 window) → TD-4 (Pi 3 + PiTFT deployment, one systemd service).

- [x] TD-2 Prepare display assets for the dimming-rectangle render model
  New model: **one "all-segments-lit" bitmap per instrument**, darkened by dim
  rectangles. Drops the old 21-frame PNG export entirely. Art source =
  `graphics/*.afdesign`; fonts named in `pyportal/README.md`. Exact pixel
  dimensions / segment-boundary coordinates pending (see TODO.md "Pending input").
  Delivered as a **single combined `claude_o_meter/assets/background.png`**
  (480×320, all instruments lit in one bitmap) rather than three separate
  per-instrument exports — a simplification by the art. Loaded via
  `claude_o_meter/assets.py`. NOTE: the tach is a **curved arc**, not a straight
  horizontal bar — the single-rectangle `reveal_segments` h-variant won't dim it
  cleanly; per-segment dimming is a TD-3.4 design question (segment coords still
  pending).
  - [x] TD-2.1 Export one full-on bitmap for the **horizontal 20-segment tach bar**
        (blue/yellow/red bands as today) into `claude_o_meter/assets/`.
        Delivered lit within the combined `background.png` (curved-arc form).
  - [x] TD-2.2 Export one full-on bitmap for the **vertical 20-segment fuel gauge**.
        Delivered lit within the combined `background.png`.
  - [x] TD-2.3 Export the **warning lights** in their lit state — "low fuel" and
        "check engine" — to be dimmed-when-off via the same overlay mechanism.
        Delivered lit within the combined `background.png`.
  - [x] TD-2.4 Place the two fonts as TTF/OTF in `claude_o_meter/assets/fonts/`
        (DESG7Modern-Italic for the 0–99 readout + dollar amounts; Dogica-Pixel
        for labels / messages / reset times). Sizes pending pixel spec. Drop the
        `otf2bdf` step.
        Done: DSEG7 Modern **Mini Italic** (0–99 readout) + Modern **Mini Bold
        Italic** (dollar amounts + reset date/time); **Roboto Condensed Bold
        Italic** substitutes for Dogica-Pixel (labels). Non-Mini DSEG7 Modern
        faces kept as alternates. Each family kept with its SIL OFL license;
        web formats dropped. Provisional sizes in `layout.py`.

- [ ] TD-3 Build the pygame display half (`claude_o_meter/`) — the full instrument cluster
  Port pure logic verbatim; delete all ESP32/WiFi code. Runs in the same process
  as the TD-1 poll thread and reads `state.snapshot` directly (no `requests`, no
  HTTP). Develop on the Mac in a **windowed 480×320 SDL surface** against the
  `fake` data source. Use named layout constants so the pending pixel/font spec
  can drop in later without restructuring.
  - [x] TD-3.1 Add `render.py` and `layout.py` (pixel constants + segment
        boundaries) to the package. `main.py` opens a 480×320 window and runs the
        pygame loop on the main thread, reading the shared `state.snapshot` each
        frame.
        Done: `layout.py` (named provisional constants — exact pixels pending),
        `render.py` (`render_frame()` skeleton clearing to bg; widgets land in
        TD-3.3..3.8), `main.py` `run_display()` runs the main-thread pygame loop
        reading `state.snapshot`. Headless-verified via SDL dummy driver in
        `tests/test_display_loop.py` (2 tests).
  - [x] TD-3.2 Port pure helpers verbatim from `code.py`: `tach_position()`,
        `fmt_hhmm()`, `fmt_duration()`, `_clamp01()`. Tach keeps the `redline_ratio`
        mapping and knobs (`REDLINE_FRAME`, `BLUE_EXPONENT`, `RED_FULL_RATIO`).
        Done in `claude_o_meter/gauges.py` (pygame-free); `fmt_hhmm` takes an
        explicit `utc_offset_hours` arg (was a module global). 9 unit tests in
        `tests/test_gauges.py`.
  - [x] TD-3.3 Dimming primitive: a reusable "reveal N of M segments" helper that
        blits a full-on bitmap then a black `SRCALPHA` rectangle whose edge **snaps
        to a segment boundary**. Right-pinned (horizontal) and top-pinned (vertical)
        variants. Opacity tunable, default alpha≈212 (~83%, matches current ghost).
        Done: superseded by explicit-geometry helpers once Josh supplied the real
        coordinates — `render.dim_rect(surface, rect, opacity)` (low-level) plus
        `dim_tach`/`dim_fuel` reading per-instrument geometry from `layout.py`.
        Fractional lit rounds to a segment boundary; opacity from `config.toml`'s
        `DIM_OPACITY`. Tests in `tests/test_dimming.py`.
  - [x] TD-3.4 Horizontal tach bar + 0–99 readout: segment count and number both
        driven by `redline_ratio` via `tach_position()` (mirrors `update_tach`).
        Number = DESG7 font, dark "88" ghost + live value overlay.
        Done: bar = `render.dim_tach` (geometry left0=10, pitch=20, y 16..286,
        right=403). Number = `render.draw_tach_number` from `gauges.tach_number`
        (round(tach_position/20*99)): DSEG7 Modern Mini Italic 80pt, dim "88"
        ghost (blue precomputed as C_LIGHT·(255−DIM_OPACITY)/255) with the live
        value bright, right-aligned in the two-digit field; visible "88" top-left
        at `NUM_POS` (190,172). Both wired into `render_frame`.
  - [x] TD-3.5 Vertical fuel gauge: `fuel = clamp(100 − seven_day.utilization, 0,
        100)`, quantized to 20 segments, draining top→bottom (top-pinned dim).
        Done: `gauges.fuel_segments(utilization)` (pure, clamped, linear) →
        `render.dim_fuel`, geometry (bottom0=220, pitch=8, x 422..456, top=63) in
        `layout.py`; wired into `render_frame`. Verified via the reveal demo +
        unit tests.
  - [x] TD-3.6 Low-fuel light: lit when remaining ≤ 20% (`utilization ≥ 80`),
        else dimmed.
        Done: `render.dim_low_fuel(surface, on)` over `LOW_FUEL_RECT`
        (416,232)-(464,278); `render_frame` lights it when `seven_day_pct ≥ 80`.
  - [x] TD-3.7 Money + reset readouts: extra-use $, extra-limit $, balance $ (USD
        from the snapshot; format `$X.XX`, clamp ≥999.99 defensively); 7-day reset
        date; 5-hour reset time (`fmt_hhmm`). USD only.
    - [x] TD-3.7.a Money readouts (extra-use / extra-limit / balance $). Each is a
          four-element group at a fixed top-left: "$" (Roboto Cond. Bold Italic
          15pt @ +(0,3)), the value over a dim "888 88" ghost (DSEG7 Modern Mini
          Bold Italic 20pt @ +(8,0)), "." (Roboto 32pt @ +(55,15)), and the label
          (Roboto 15pt @ +(95,5)). Groups at (10,289)/(170,289)/(328,289).
          `gauges.fmt_money` formats the 6-char field `"DDD CC"` (space = decimal,
          dollars space-padded, clamp 999.99); `render.draw_money_group` packs the
          three dollar digits in digit cells (DSEG space adv 4 ≠ digit 16, so
          leading blanks register on the ghost) then a natural space before the
          two cent digits, with the "." overlaying that gap. `render_frame` shows
          the money row when healthy, the fault message when faulted. Tests in
          `tests/test_money.py`.
    - [x] TD-3.7.b Reset readouts + static labels (top area, always drawn). 7-day
          reset date `"YYYY  MM  DD"` (DSEG7 Modern Mini Bold Italic 20pt @ (11,30))
          over the dim "8888  88  88" ghost, with the "7 Day Reset" label (Roboto
          15pt @ (11,12)). 5-hour reset time `"HH:MM"` (same DSEG face @ (11,88))
          over "88:88", label "5 Hour Reset" (@ (11,71)). Plus the fuel-gauge "7
          Day" label (@ (422,36)) and two "-" separators (@ (77,39)/(77,118)).
          `gauges.fmt_date` (pure, `time.gmtime`, two-space groups, None→blank) +
          existing `fmt_hhmm`, both offset by `cfg.utc_offset_hours`.
          `render.draw_dseg_string` anchors the ghost ink top-left at the position
          and draws the same-structure live string at the shared origin (no
          per-cell packing needed — date/time always have every digit). All in
          `render.draw_resets`, called unconditionally in `render_frame`. Tests in
          `tests/test_resets.py`.
  - [x] TD-3.8 Fault state machine reading the snapshot: map
        poll-failure / data-stale (`snapshot.stale`) / needs-auth
        (`snapshot.auth_failed`) → check-engine light + a distinct message each;
        billing-feed failures excluded. **Delete** `wifi_kickoff`/`wifi_finish`/
        `wifi_recover` and all ESP32 reset logic — there is no network layer in the
        display half anymore.
        Done: `faults.fault_message(snapshot)` (pure) → three distinct messages by
        priority — `NEEDS AUTH` (`auth_failed`) > `NO DATA` (`last_update==0`,
        never polled = poll-failure) > `DATA STALE` (`stale` with prior data).
        `render_frame` drives both the check-engine light (`dim_check_engine` over
        `CHECK_ENGINE_RECT`, tach dim hole-punched so it shines on a fault) and the
        bottom message from this one signal. Billing-feed failures never set
        `stale`/`auth_failed` (poller), so they can't trip a fault. Message =
        Roboto Condensed Bold Italic 15pt in project blue (#40A9BF), text-box
        top-left at (10,296). Text is anchored by font line-box metrics (not ink)
        via `draw_text`, so every message shares one baseline; positions are given
        as the Affinity top-left (72 DPI → pt = px). (No wifi code to delete.)
  - [x] TD-3.9 Verify on the Mac (windowed 480×320, `fake` source): tach, fuel
        gauge, both lights, money/reset readouts, and the check-engine fault
        overlay all animate through the fake source's cycles. This is the
        desktop-supported run target, not just a test.
        Done: the fake source couldn't drive every widget (7-day % topped out at
        60 so the low-fuel light never lit; `error` was always None so the
        check-engine light/message never showed; the loop slept the 60s poll
        cadence so the gauges barely moved). Reworked `fakesource.py` into a pure
        `fake_values(elapsed, now)` (swept fields) + a thin `fake_loop` ticking
        every `TICK_SECONDS` (0.2s) so the window animates; widened the 7-day
        sweep to 5..95 (crosses the 80% low-fuel threshold) and added a per-cycle
        fault window rotating None→No Data / Auth / Connection / Stale. `main`
        now starts `fake_loop()` on its own tick (not the poll cadence). Verified
        three ways: `tests/test_fakesource.py` sweeps a full set of cycles and
        asserts every widget/light/fault is exercised; a headless render of
        representative phases to PNG was eyeballed (tach gradient, fuel drain,
        both lights toggling, money row, and each fault message all correct).

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
