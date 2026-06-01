# TODO — Backlog

Enhancements once the core path (TODO_CRITICAL) runs end-to-end on the Pi 3.

- [ ] TD-5 Optional richer 7-day history view
  `server/src/api.py` already serves `/history` (hourly 5h peaks via
  `store.hourly_peaks`). The redesign represents the 7-day window as the fuel
  gauge (TD-3.5), so this is no longer the primary 7d display — but an hourly
  histogram strip remains a possible "trend" addition if screen space allows.
  Carry the leftover `HISTORY_REFRESH_EVERY_N_POLLS` knob from
  `pyportal/settings.toml.example` into `config.toml` if pursued.

- [ ] TD-6 Backlight dimming for fault states
  `code.py` used `board.DISPLAY.brightness` (no pygame equivalent). PiTFT
  backlight is on GPIO 18. Lower-priority now that the check-engine light +
  message (TD-3.8) carry fault signalling on their own.
  - [ ] TD-6.1 Drive backlight brightness via hardware PWM on GPIO 18
        (`rpi-backlight` / `pigpio`) to dim the whole panel in fault states.
  - [ ] TD-6.2 Fallback: if PWM is unavailable, dim by blitting a full-screen
        translucent overlay on top of the cluster. Default chosen in `config.toml`.

- [ ] TD-7 Spike: can plain `httpx` replace `curl_cffi` past Cloudflare?
  curl_cffi exists only to mimic Chrome's TLS fingerprint. Test (5 min) whether
  `httpx` + the sessionKey cookie + Chrome-ish headers gets a 200 from
  `claude.ai/api/.../usage` AND `/prepaid/credits`. If yes, dropping curl_cffi
  removes native-wheel concerns. If 403, keep it. Nice-to-have, NOT a dependency
  of TD-1/TD-12 — the fingerprint rejection is why it was chosen and can regress.

- [ ] TD-8 Retire PyPortal artifacts once the Pi path is proven
  Only after TD-1..TD-4 are confirmed working on hardware. Move, don't delete
  prematurely — keep `graphics/*.afdesign` as art source-of-truth.
  - [ ] TD-8.1 Remove `pyportal/` (code.py, bmp/, fonts/, requirements.txt, settings).
  - [ ] TD-8.2 Remove `graphics/png_to_bmp.py` (BMP conversion no longer needed).
  - [ ] TD-8.3 Remove `server/Dockerfile` + `docker-compose.yml` (replaced by
        systemd in TD-1.3), unless keeping Docker as a documented alternative.
  - [ ] TD-8.4 Update top-level `README.md` architecture diagram + quick-start to
        the Pi 3 two-service layout and the new instrument cluster.

- [ ] TD-9 Mac dev loop documentation
  Capture the develop-on-Mac workflow (run `mock_server.py`, point display
  `config.toml` at it, windowed SDL) in `display/README.md` so the renderer can
  be iterated without a Pi or a live cookie.
