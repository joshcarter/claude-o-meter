"""Reset readouts: date/time formatting + ghosted DSEG rendering (TD-3.7.b)."""

import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from claude_o_meter import gauges, layout, render  # noqa: E402
from claude_o_meter.config import load_config  # noqa: E402
from claude_o_meter.state import Snapshot  # noqa: E402


def test_fmt_date_field():
    ts = 1_780_000_000  # some 2026 timestamp
    out = gauges.fmt_date(ts)
    assert out == time.strftime("%Y  %m  %d", time.gmtime(ts))  # two-space groups
    assert len(out) == 12 and out[4:6] == "  " and out[8:10] == "  "
    assert gauges.fmt_date(None) == ""   # missing → blank (ghost only)
    assert gauges.fmt_date(0) == ""
    # The offset shifts the calendar day across a midnight boundary.
    midnight = 1_780_000_000 - (1_780_000_000 % 86400)   # 00:00 UTC
    assert gauges.fmt_date(midnight, -1) != gauges.fmt_date(midnight, 0)


def _alpha():
    return pygame.Surface((layout.SCREEN_W, layout.SCREEN_H), pygame.SRCALPHA)


def test_dseg_string_ghost_anchored_and_layered():
    pygame.init()
    try:
        surf = _alpha()
        cfg = load_config()
        font = render.get_font(layout.FONT_MONEY, layout.RESET_FIELD_PT)
        render.draw_dseg_string(surf, layout.TIME_GHOST, "12:34", font, (50, 80), cfg)
        ink = surf.get_bounding_rect()
        assert ink.topleft == (50, 80)            # ghost ink top-left at pos
        found_ghost = found_live = False
        for y in range(ink.top, ink.bottom):
            for x in range(ink.left, ink.right):
                _, _, b, a = surf.get_at((x, y))
                if a < 10:
                    continue
                if b > 150:
                    found_live = True
                elif 20 < b < 60:
                    found_ghost = True
        assert found_ghost and found_live
    finally:
        pygame.quit()


def test_dseg_string_blank_live_shows_ghost_only():
    pygame.init()
    try:
        surf = _alpha()
        cfg = load_config()
        font = render.get_font(layout.FONT_MONEY, layout.RESET_FIELD_PT)
        render.draw_dseg_string(surf, layout.DATE_GHOST, "", font, (11, 30), cfg)
        # Only the dim ghost is present — no bright live pixels.
        bright = False
        ink = surf.get_bounding_rect()
        for y in range(ink.top, ink.bottom):
            for x in range(ink.left, ink.right):
                _, _, b, a = surf.get_at((x, y))
                if a > 10 and b > 150:
                    bright = True
        assert ink.height > 0 and not bright
    finally:
        pygame.quit()


def test_resets_drawn_in_render_frame():
    pygame.init()
    try:
        cfg = load_config()
        surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
        snap = Snapshot(stale=False, last_update=1, five_hour_resets_at=1_780_000_000,
                        seven_day_resets_at=1_780_500_000)
        render.render_frame(surf, snap, cfg)
        # "7 Day Reset" label sits near (11, 12); expect blue ink in that band.
        blue = False
        for y in range(10, 28):
            for x in range(11, 110):
                r, _, b = surf.get_at((x, y))[:3]
                if b > 150 and b > r * 2:
                    blue = True
        assert blue
    finally:
        pygame.quit()
