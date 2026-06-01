"""Headless verification of the pygame display skeleton (TD-3.1).

Runs the loop against the SDL dummy video driver so it needs no real display.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from claude_o_meter import assets, layout, render  # noqa: E402
from claude_o_meter.config import load_config  # noqa: E402
from claude_o_meter.main import run_display  # noqa: E402
from claude_o_meter.state import Snapshot  # noqa: E402


def test_render_frame_draws_background():
    import pygame

    pygame.init()
    try:
        surface = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
        surface.fill((123, 45, 67))
        render.render_frame(surface, Snapshot(), load_config())
        bg = assets.load_image(layout.BACKGROUND)
        # The cluster bitmap is blitted whole: black corners and the lit blue
        # tach band both match the source art.
        assert surface.get_at((0, 0))[:3] == (0, 0, 0)
        assert surface.get_at((240, 40))[:3] == bg.get_at((240, 40))[:3]
        assert surface.get_at((240, 40))[:3] == layout.C_LIGHT
    finally:
        pygame.quit()


def test_run_display_bounded_frames():
    cfg = load_config()
    frames = run_display(cfg, max_frames=3)
    assert frames == 3
