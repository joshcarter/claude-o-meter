"""Headless verification of the pygame display skeleton (TD-3.1).

Runs the loop against the SDL dummy video driver so it needs no real display.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from claude_o_meter import layout, render  # noqa: E402
from claude_o_meter.config import load_config  # noqa: E402
from claude_o_meter.main import run_display  # noqa: E402
from claude_o_meter.state import Snapshot  # noqa: E402


def test_render_frame_clears_to_background():
    import pygame

    pygame.init()
    try:
        surface = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
        surface.fill((123, 45, 67))
        render.render_frame(surface, Snapshot(), load_config())
        assert surface.get_at((0, 0))[:3] == layout.C_BG
        assert surface.get_at((layout.SCREEN_W - 1, layout.SCREEN_H - 1))[:3] == layout.C_BG
    finally:
        pygame.quit()


def test_run_display_bounded_frames():
    cfg = load_config()
    frames = run_display(cfg, max_frames=3)
    assert frames == 3
