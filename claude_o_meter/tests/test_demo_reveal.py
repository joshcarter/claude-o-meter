"""Smoke test for the manual reveal demo's frame builder.

demo_reveal isn't part of the app's render path, so a signature change in
render (e.g. dim_fuel gaining required args) can break it without any other
test noticing. This exercises every _draw phase headlessly so that regression
surfaces here instead of only when a human runs the demo.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from claude_o_meter import demo_reveal, layout  # noqa: E402
from claude_o_meter.config import load_config  # noqa: E402


def test_demo_reveal_draw_all_phases():
    pygame.init()
    try:
        # _draw ends in pygame.display.flip(), so a display surface is required
        # (the dummy SDL driver provides one offscreen).
        surf = pygame.display.set_mode((layout.SCREEN_W, layout.SCREEN_H))
        cfg = load_config()
        # The three phases the demo drives: fully dimmed, tach full / fuel
        # partway, and the warning-light combinations.
        demo_reveal._draw(surf, cfg, 0, 0)
        demo_reveal._draw(surf, cfg, layout.TACH_SEGMENTS, layout.FUEL_SEGMENTS)
        demo_reveal._draw(surf, cfg, 12, 10, ce_on=True, lf_on=True)
    finally:
        pygame.quit()
