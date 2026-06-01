"""0–99 tach readout: value mapping + ghost/live rendering (TD-3.4)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from claude_o_meter import layout, render  # noqa: E402
from claude_o_meter.config import load_config  # noqa: E402
from claude_o_meter.gauges import tach_number  # noqa: E402


def test_tach_number_mapping():
    assert tach_number(None) == 0
    assert tach_number(0) == 0
    assert tach_number(2.0) == 99        # redline pegs the readout at 99
    assert tach_number(10.0) == 99       # beyond peg stays 99
    prev = -1
    for r in [0.0, 0.1, 0.5, 1.0, 1.5, 2.0]:
        v = tach_number(r)
        assert 0 <= v <= 99 and v >= prev
        prev = v


def test_readout_ghost_anchored_at_num_pos():
    pygame.init()
    try:
        surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H), pygame.SRCALPHA)
        render.draw_tach_number(surf, 88, load_config())
        assert surf.get_bounding_rect().topleft == layout.NUM_POS
    finally:
        pygame.quit()


def test_readout_has_dim_ghost_and_bright_live():
    pygame.init()
    try:
        surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H), pygame.SRCALPHA)
        render.draw_tach_number(surf, 11, load_config())  # many segments off → ghost shows
        rect = surf.get_bounding_rect()
        found_ghost = found_live = False
        for y in range(rect.top, rect.bottom):
            for x in range(rect.left, rect.right):
                _, _, b, a = surf.get_at((x, y))
                if a < 10:
                    continue
                if b > 150:
                    found_live = True       # bright C_LIGHT segments (live)
                elif 20 < b < 60:
                    found_ghost = True       # precomputed dim ghost (b≈32)
        assert found_ghost and found_live
    finally:
        pygame.quit()


def test_readout_single_digit_right_aligned():
    pygame.init()
    try:
        surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H), pygame.SRCALPHA)
        render.draw_tach_number(surf, 8, load_config())   # 1 digit → ones place
        field = surf.get_bounding_rect()                  # spans both ghost digits
        sx = n = 0
        for y in range(field.top, field.bottom):
            for x in range(field.left, field.right):
                _, _, b, a = surf.get_at((x, y))
                if a > 10 and b > 150:                     # bright live pixels
                    sx += x
                    n += 1
        assert n > 0 and sx / n > field.centerx           # live sits right of centre
    finally:
        pygame.quit()
