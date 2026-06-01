"""Money readouts: USD field formatting + group rendering (TD-3.7)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from claude_o_meter import layout, render  # noqa: E402
from claude_o_meter.config import load_config  # noqa: E402
from claude_o_meter.gauges import fmt_money  # noqa: E402
from claude_o_meter.state import Snapshot  # noqa: E402


def test_fmt_money_field():
    assert fmt_money(12.34) == " 12 34"     # dollars space-padded, cents 2-wide
    assert fmt_money(5.0) == "  5 00"
    assert fmt_money(0.5) == "  0 50"
    assert fmt_money(0) == "  0 00"
    assert fmt_money(None) == "  0 00"       # missing reads as zero
    assert fmt_money(123.45) == "123 45"
    assert fmt_money(9999.99) == "999 99"    # clamped to the 3-digit field
    assert fmt_money(2.005) == "  2 00" or fmt_money(2.005) == "  2 01"  # rounds


def _alpha_surface():
    return pygame.Surface((layout.SCREEN_W, layout.SCREEN_H), pygame.SRCALPHA)


def test_money_group_anchored_and_layered():
    pygame.init()
    try:
        surf = _alpha_surface()
        gx, gy = (40, 200)
        render.draw_money_group(surf, 12.34, "Extra", (gx, gy), load_config())
        ink = surf.get_bounding_rect()
        # Group's left-most ink is the "$" at offset (0, 3); top edge near gy.
        assert abs(ink.left - gx) <= 2
        assert ink.top >= gy and ink.top <= gy + 6

        # Both a dim ghost (b≈32) and bright live digits (b>150) are present.
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


def test_render_frame_shows_money_when_healthy():
    pygame.init()
    try:
        cfg = load_config()
        surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
        snap = Snapshot(stale=False, last_update=1, five_hour_redline_ratio=0.5,
                        seven_day_pct=40.0, extra_usage_used=12.34,
                        extra_usage_limit=50.0, balance=7.5)
        render.render_frame(surf, snap, cfg)
        # Bright blue money ink appears in each of the three group columns.
        def has_blue(x0, x1):
            for y in range(285, layout.SCREEN_H):
                for x in range(x0, x1):
                    r, _, b = surf.get_at((x, y))[:3]
                    if b > 150 and b > r * 2:
                        return True
            return False
        assert has_blue(10, 130)     # Extra
        assert has_blue(170, 290)    # Limit
        assert has_blue(328, 448)    # Balance
    finally:
        pygame.quit()


def test_render_frame_hides_money_on_fault():
    pygame.init()
    try:
        cfg = load_config()
        surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
        # Never-polled → NO DATA fault: the bottom strip shows the message, not
        # the money groups (no "$" ink far right where Balance would sit).
        render.render_frame(surf, Snapshot(stale=True, last_update=0), cfg)
        balance_blue = False
        for y in range(285, layout.SCREEN_H):
            for x in range(328, 448):
                r, _, b = surf.get_at((x, y))[:3]
                if b > 150 and b > r * 2:
                    balance_blue = True
        assert not balance_blue
    finally:
        pygame.quit()
