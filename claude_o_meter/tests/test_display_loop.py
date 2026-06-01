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
        # Full-scale snapshot: tach pegged (no tach dim), tank full (no fuel dim),
        # so the lit cluster bitmap shows through unchanged.
        snap = Snapshot(five_hour_redline_ratio=2.0, seven_day_pct=0.0)
        render.render_frame(surface, snap, load_config())
        bg = assets.load_image(layout.BACKGROUND)
        assert surface.get_at((0, 0))[:3] == (0, 0, 0)
        assert surface.get_at((240, 40))[:3] == bg.get_at((240, 40))[:3]
        assert surface.get_at((240, 40))[:3] == layout.C_LIGHT
    finally:
        pygame.quit()


def test_render_frame_dims_when_empty():
    import pygame

    pygame.init()
    try:
        surface = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
        # No data → tach 0 lit, so the lit blue band at (240,40) is dimmed.
        render.render_frame(surface, Snapshot(), load_config())
        assert surface.get_at((240, 40))[:3] != layout.C_LIGHT
    finally:
        pygame.quit()


def test_render_frame_toggles_warning_lights():
    import pygame

    pygame.init()
    try:
        cfg = load_config()

        def value_at(snap, x, y):
            surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
            render.render_frame(surf, snap, cfg)
            return surf.get_at((x, y))[0]

        # Check-engine: lit on a fault, dimmed when healthy. last_update=1 keeps
        # the healthy snapshot out of the "no data" fault. Sampled at a lit pixel
        # of the icon (376,235); the tach dim excludes this rect.
        ce_on = value_at(Snapshot(error="Data Stale", last_update=1), 376, 235)
        ce_off = value_at(Snapshot(last_update=1), 376, 235)
        assert ce_on > ce_off

        # Low-fuel: lit when 7-day utilisation ≥ 80%. Sampled at (447,235).
        lf_on = value_at(Snapshot(last_update=1, seven_day_pct=90.0), 447, 235)
        lf_off = value_at(Snapshot(last_update=1, seven_day_pct=10.0), 447, 235)
        assert lf_on > lf_off
    finally:
        pygame.quit()


def test_run_display_bounded_frames():
    cfg = load_config()
    frames = run_display(cfg, max_frames=3)
    assert frames == 3
