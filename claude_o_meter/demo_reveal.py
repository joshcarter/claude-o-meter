"""Manual visual check: reveal the tach bars, then the fuel bars, then the
warning lights (including the check-engine light shining through a dimmed tach),
then the bottom fault messages.

On a desktop it opens a real 480×320 window. On the Pi PiTFT (Raspberry Pi OS
Lite, no X) set ``DISPLAY_MODE=framebuffer`` so it renders offscreen and copies
each frame to ``FB_DEVICE`` (``/dev/fb1`` by default) — same path as the main
app. Run it from the repo root:

    python -m claude_o_meter.demo_reveal           # default 150 ms/step
    python -m claude_o_meter.demo_reveal 300        # slower

    # On the Pi:
    DISPLAY_MODE=framebuffer python -m claude_o_meter.demo_reveal

Close the window or press Esc/Q to quit early (Ctrl-C on the framebuffer).
"""

import os
import sys
import time

import pygame

from . import layout, render
from .config import load_config
from .state import Snapshot

# Set in main() when DISPLAY_MODE=framebuffer; importing pygame is display-free,
# so only init()/set_mode() below need the SDL driver chosen first.
_fb = None


def _present(surface):
    """Push a finished frame: framebuffer copy on the Pi, window flip otherwise."""
    if _fb is not None:
        _fb.blit(surface)
    else:
        pygame.display.flip()


def _draw(surface, cfg, tach_lit, fuel_lit, ce_on=False, lf_on=False):
    surface.fill(layout.C_BG)
    surface.blit(render._get_background(), (0, 0))
    render.dim_tach(surface, tach_lit, cfg.dim_opacity)
    render.draw_tach_number(surface, round(tach_lit / layout.TACH_SEGMENTS * 99), cfg)
    # Three stacked fuel gauges (top→bottom): 5-hour, 7-day, Fable.
    render.dim_fuel(surface, fuel_lit, layout.FUEL_5H_DIM_TOP, layout.FUEL_5H_DIM_BOTTOM,
                    cfg.dim_opacity)
    render.dim_fuel(surface, fuel_lit, layout.FUEL_7D_DIM_TOP, layout.FUEL_7D_DIM_BOTTOM,
                    cfg.dim_opacity)
    render.dim_fuel(surface, fuel_lit, layout.FUEL_FABLE_DIM_TOP, layout.FUEL_FABLE_DIM_BOTTOM,
                    cfg.dim_opacity)
    render.dim_low_fuel(surface, lf_on, cfg.dim_opacity)
    render.dim_check_engine(surface, ce_on, cfg.dim_opacity)
    _present(surface)


def _wants_quit():
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            return True
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_q):
            return True
    return False


def main(delay_ms=10):
    global _fb
    cfg = load_config()

    framebuffer_mode = cfg.display_mode == "framebuffer"
    if framebuffer_mode:
        # Render offscreen and copy to the panel — no X server / window needed.
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.init()
    surface = pygame.display.set_mode((layout.SCREEN_W, layout.SCREEN_H))
    pygame.display.set_caption("claude-o-meter — reveal demo")
    if framebuffer_mode:
        from .framebuffer import Framebuffer

        _fb = Framebuffer(cfg.fb_device, layout.SCREEN_W, layout.SCREEN_H)
    try:
        # Start fully dimmed.
        _draw(surface, cfg, 0, 0)
        pygame.time.delay(delay_ms * 3)

        # Reveal the tach bars one at a time (fuel stays empty).
        for lit in range(1, layout.TACH_SEGMENTS + 1):
            if _wants_quit():
                return
            _draw(surface, cfg, lit, 0)
            pygame.time.delay(delay_ms)
        pygame.time.delay(delay_ms * 2)

        # Reveal the fuel bars one at a time (tach stays full).
        for lit in range(1, layout.FUEL_SEGMENTS + 1):
            if _wants_quit():
                return
            _draw(surface, cfg, layout.TACH_SEGMENTS, lit)
            pygame.time.delay(delay_ms)
        pygame.time.delay(delay_ms * 2)

        # Warning lights. Tach left partially dimmed (12) so the check-engine
        # light sits under the tach dim — it must still light cleanly.
        hold = delay_ms * 4
        for ce_on, lf_on in [(False, False), (True, False), (False, True), (True, True)]:
            if _wants_quit():
                return
            _draw(surface, cfg, 12, 10, ce_on=ce_on, lf_on=lf_on)
            pygame.time.delay(hold)
        pygame.time.delay(hold)

        # Bottom status area: the full snapshot pipeline, cycling fault messages
        # (healthy → no message; stale; never-polled; auth failure).
        for snap in [
            Snapshot(last_update=1, five_hour_redline_ratio=1.25, seven_day_pct=50.0,
                     extra_usage_used=12.34, extra_usage_limit=50.0, balance=7.5,
                     five_hour_resets_at=int(time.time()) + 3 * 3600,
                     seven_day_resets_at=int(time.time()) + 5 * 86400),
            # Snapshot(last_update=1, error="Data Stale", five_hour_redline_ratio=0.5, seven_day_pct=40.0),
            # Snapshot(last_update=0, five_hour_redline_ratio=0.5, seven_day_pct=40.0),
            # Snapshot(error="Authorization Failed", five_hour_redline_ratio=0.5, seven_day_pct=40.0),
        ]:
            if _wants_quit():
                return
            render.render_frame(surface, snap, cfg)
            _present(surface)
            pygame.time.delay(hold)

        # Hold the final frame until the window is closed.
        while not _wants_quit():
            pygame.time.delay(50)
    finally:
        if _fb is not None:
            _fb.close()
        pygame.quit()


if __name__ == "__main__":
    delay = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    main(delay)
