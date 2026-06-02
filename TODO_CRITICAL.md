# TODO — Critical

Core path to a working **claude-o-meter** dashboard. Develop desktop-first, then
deploy the same program to the Pi 3. The desktop half is complete (TD-1, TD-12,
TD-2, TD-3 — see `DONE.md`); the remaining critical work is TD-4 (Pi 3 + PiTFT
deployment, one systemd service).

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
