# TODO — Deferred

Alternatives considered and not chosen, or blocked on input/hardware. Not read
during automated refine. Each carries an unblock condition.

- [ ] TD-13 Multi-currency support for the money readouts
  This version is USD-only; TD-12.3 treats any non-USD `currency` as unavailable.
  Full support means formatting per currency (symbol, decimal places) and not
  assuming cents=÷100 for every currency.
  **Unblock:** user wants non-USD display, or the account reports a non-USD
  `currency` from `extra_usage` / `/prepaid/credits`.

- [ ] TD-10 Browser-kiosk dashboard variant (alternative renderer)
  Considered in planning: server serves an HTML/JS dashboard, Pi runs Chromium
  fullscreen. Richest visuals but heavy for a small SPI panel and overkill on a
  Pi 3. Deferred in favor of the pygame renderer (TD-3).
  **Unblock:** user wants a large HDMI monitor instead of the 3.5" PiTFT, or
  animated CSS/SVG visuals the pygame client can't easily match.

- [ ] TD-11 Alternate host: Pi 2B or Pi Zero 2 W
  Pi 3 chosen for onboard WiFi + headroom. Pi 2B works but needs Ethernet/USB-WiFi
  and Bullseye-or-newer for the armv7l curl_cffi wheel. Pi Zero 2 W (quad A53)
  also works; the original **Pi Zero W is ruled out** — ARMv6 has no curl_cffi
  wheel and a source build is impractical there.
  **Unblock:** the chosen Pi 3 becomes unavailable and a fallback host is needed.
