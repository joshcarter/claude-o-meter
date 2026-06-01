"""Text rendering: ink-anchored placement and the bottom fault message.

Fonts use the Affinity point size directly (art is 72 DPI → 1 pt = 1 px).
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from claude_o_meter import layout, render  # noqa: E402
from claude_o_meter.config import load_config  # noqa: E402
from claude_o_meter.faults import MSG_NEEDS_AUTH  # noqa: E402
from claude_o_meter.state import Snapshot  # noqa: E402


def _alpha_surface():
    # Transparent surface so get_bounding_rect() reflects only drawn ink.
    return pygame.Surface((layout.SCREEN_W, layout.SCREEN_H), pygame.SRCALPHA)


def test_draw_text_anchors_are_metric_based():
    pygame.init()
    try:
        surf = _alpha_surface()
        font = render.get_font(layout.FONT_LABEL, layout.BOTTOM_TEXT_PT)

        # topleft: returned line-box rect starts exactly at the anchor and is a
        # full line-box tall, regardless of which glyphs are present.
        r = render.draw_text(surf, "NO DATA", font, (255, 0, 0), topleft=(10, 100))
        assert r.topleft == (10, 100)
        assert r.height == font.get_height()
        ink = surf.get_bounding_rect()
        assert r.top <= ink.top and ink.bottom <= r.bottom   # ink within the box
        assert abs(ink.left - 10) <= 1

        # bottomleft and baseline are derived from metrics, not the ink.
        r2 = render.draw_text(_alpha_surface(), "NO DATA", font, (255, 0, 0), bottomleft=(10, 296))
        assert r2.bottomleft == (10, 296)
        r3 = render.draw_text(_alpha_surface(), "NO DATA", font, (255, 0, 0), baseline_left=(10, 200))
        assert r3.top == 200 - font.get_ascent()

        # captop_left: the visible capitals start at the anchor y (not the line
        # box), so the design-tool top-left lands on the glyphs.
        s4 = _alpha_surface()
        render.draw_text(s4, "NO DATA", font, (255, 0, 0), captop_left=(10, 100))
        assert abs(s4.get_bounding_rect().top - 100) <= 1
    finally:
        pygame.quit()


def test_bottom_shows_fault_in_project_blue():
    pygame.init()
    try:
        surf = _alpha_surface()
        render.draw_bottom(surf, MSG_NEEDS_AUTH)
        ink = surf.get_bounding_rect()
        assert ink.height > 0                                  # something was drawn
        assert abs(ink.top - layout.BOTTOM_TEXT_POS[1]) <= 1   # cap top at the anchor y
        assert abs(ink.left - layout.BOTTOM_TEXT_POS[0]) <= 1
        px = surf.get_at((ink.left, ink.top + 2))
        assert px[2] > px[0]                                   # project blue: more blue than red
    finally:
        pygame.quit()


def test_bottom_blank_when_healthy():
    pygame.init()
    try:
        surf = _alpha_surface()
        render.draw_bottom(surf, None)              # no fault, money pending spec
        assert surf.get_bounding_rect().height == 0  # nothing drawn
    finally:
        pygame.quit()


def test_render_frame_draws_fault_message():
    pygame.init()
    try:
        cfg = load_config()

        def blue_in(snap, x0, x1):
            surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
            render.render_frame(surf, snap, cfg)
            for y in range(layout.BOTTOM_TEXT_POS[1], layout.SCREEN_H):
                for x in range(x0, x1):
                    r, _, b = surf.get_at((x, y))[:3]
                    if b > 120 and b > r * 2:        # project blue C_LIGHT
                        return True
            return False

        fault = Snapshot(stale=True, last_update=0)                   # NO DATA
        healthy = Snapshot(stale=False, last_update=1, balance=7.5)
        # The fault message lands at the left of the bottom strip.
        assert blue_in(fault, 10, 200)
        # When healthy, money fills the far-right Balance column; a fault leaves
        # that column dark (the message replaces the whole money row).
        assert blue_in(healthy, 328, 448)
        assert not blue_in(fault, 328, 448)
    finally:
        pygame.quit()
