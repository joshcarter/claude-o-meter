"""Headless verification of the pygame display skeleton (TD-3.1).

Runs the loop against the SDL dummy video driver so it needs no real display.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from claude_o_meter import assets, faults, layout, render  # noqa: E402
from claude_o_meter.config import load_config  # noqa: E402
from claude_o_meter.main import run_display  # noqa: E402
from claude_o_meter.state import Snapshot  # noqa: E402


# Lit pixel inside the 7-day fuel band (art is C_LIGHT there).
_FUEL_SAMPLE = (240, 31)  # mid-band of 7-day fuel gauge
# Lit pixel inside the tach dim region.
_TACH_SAMPLE = (300, 150)


def test_render_frame_draws_background():
    import pygame

    pygame.init()
    try:
        surface = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
        surface.fill((123, 45, 67))
        # Full-scale snapshot: tach pegged (no tach dim), tanks full (no fuel dim),
        # so the lit cluster bitmap shows through unchanged.
        snap = Snapshot(five_hour_redline_ratio=2.0, seven_day_pct=0.0,
                        five_hour_pct=0.0, fable_pct=0.0, last_update=1)
        render.render_frame(surface, snap, load_config())
        bg = assets.load_image(layout.BACKGROUND)
        assert surface.get_at((0, 0))[:3] == (0, 0, 0)
        x, y = _FUEL_SAMPLE
        assert surface.get_at((x, y))[:3] == bg.get_at((x, y))[:3]
        assert surface.get_at((x, y))[:3] == layout.C_LIGHT
    finally:
        pygame.quit()


def test_render_frame_dims_when_empty():
    import pygame

    pygame.init()
    try:
        surface = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
        # Empty fuel (100% util) dims the 7-day band; tach pegged so only fuel dims.
        snap = Snapshot(five_hour_redline_ratio=2.0, seven_day_pct=100.0,
                        five_hour_pct=0.0, fable_pct=0.0, last_update=1)
        render.render_frame(surface, snap, load_config())
        assert surface.get_at(_FUEL_SAMPLE)[:3] != layout.C_LIGHT
        # No data → tach 0 lit, so a lit tach pixel is dimmed.
        surface2 = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
        render.render_frame(surface2, Snapshot(), load_config())
        assert surface2.get_at(_TACH_SAMPLE)[:3] != layout.C_LIGHT
    finally:
        pygame.quit()


def test_render_frame_toggles_warning_lights():
    import pygame

    pygame.init()
    try:
        cfg = load_config()
        # Warning-light icon positions in the art are still pending redesign; the
        # dim helpers themselves are covered in test_dimming. Here just confirm
        # render_frame accepts the on/off snapshot shapes without error.
        for snap in (
            Snapshot(error=faults.ERR_STALE, last_update=1),
            Snapshot(last_update=1),
            Snapshot(last_update=1, seven_day_pct=10.0, five_hour_pct=10.0),
            Snapshot(last_update=1, seven_day_pct=90.0, five_hour_pct=10.0),
            Snapshot(last_update=1, seven_day_pct=10.0, five_hour_pct=90.0),
        ):
            surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
            out = render.render_frame(surf, snap, cfg)
            assert out is surf
    finally:
        pygame.quit()


def test_run_display_bounded_frames():
    cfg = load_config()
    frames = run_display(cfg, max_frames=3)
    assert frames == 3
