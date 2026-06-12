"""Tests for the segment-dimming helpers dim_rect/dim_tach/dim_fuel (TD-3.3–3.5).

A solid-colour surface stands in for the cluster bitmap so dimming is
detectable on every pixel (dimming the black art would be invisible). The exact
dim-edge positions come from the geometry in layout.py.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from claude_o_meter import layout, render  # noqa: E402

LIT = (200, 200, 200)


def _surface():
    pygame.init()
    surf = pygame.Surface((layout.SCREEN_W, layout.SCREEN_H))
    surf.fill(LIT)
    return surf


def _dimmed(surf, x, y):
    return surf.get_at((x, y))[0] < LIT[0]


# --- dim_rect ---------------------------------------------------------------

def test_dim_rect_empty_is_noop():
    surf = _surface()
    render.dim_rect(surf, (50, 50, 0, 40))
    render.dim_rect(surf, (50, 50, 40, -3))
    assert surf.get_at((50, 50))[:3] == LIT


def test_dim_rect_full_opacity_blacks_out():
    surf = _surface()
    render.dim_rect(surf, (10, 10, 20, 20), opacity=255)
    assert surf.get_at((15, 15))[:3] == (0, 0, 0)


# --- dim_tach: left edge = 10 + 20*lit, spans y 16..286 ---------------------

def test_tach_zero_lit_dims_from_x10():
    surf = _surface()
    render.dim_tach(surf, 0)
    assert _dimmed(surf, 11, 150)      # inside dim (x≥10)
    assert _dimmed(surf, 402, 150)     # up to the right edge (403)
    assert not _dimmed(surf, 200, 10)  # above the dim top (16)
    assert not _dimmed(surf, 200, 300)  # below the dim bottom (286)


def test_tach_one_lit_edge_at_x30():
    surf = _surface()
    render.dim_tach(surf, 1)
    assert not _dimmed(surf, 29, 150)  # revealed (left of edge x=30)
    assert _dimmed(surf, 31, 150)      # dimmed (right of edge)


def test_tach_two_lit_edge_at_x50():
    surf = _surface()
    render.dim_tach(surf, 2)
    assert not _dimmed(surf, 49, 150)
    assert _dimmed(surf, 51, 150)


def test_tach_fractional_rounds_to_boundary():
    a = _surface()
    render.dim_tach(a, 1.4)            # → 1, edge at x=30
    assert not _dimmed(a, 29, 150) and _dimmed(a, 31, 150)
    b = _surface()
    render.dim_tach(b, 1.6)            # → 2, edge at x=50
    assert not _dimmed(b, 49, 150) and _dimmed(b, 51, 150)


def test_tach_full_lit_no_dim():
    surf = _surface()
    render.dim_tach(surf, 20)
    assert not _dimmed(surf, 200, 150)


# --- dim_fuel (default = 7D gauge): bottom edge = 220 - 8*lit, x 447..461, top 63

def test_fuel_zero_lit_dims_to_y220():
    surf = _surface()
    render.dim_fuel(surf, 0)
    assert _dimmed(surf, 454, 64)      # just below top (63)
    assert _dimmed(surf, 454, 219)     # near the bottom (220)
    assert not _dimmed(surf, 454, 62)  # above the dim top
    assert not _dimmed(surf, 445, 150)  # left of the gauge (447)


def test_fuel_one_lit_bottom_at_y212():
    surf = _surface()
    render.dim_fuel(surf, 1)
    assert _dimmed(surf, 454, 211)     # still dimmed above the edge
    assert not _dimmed(surf, 454, 213)  # revealed below the edge (y>212)


def test_fuel_two_lit_bottom_at_y204():
    surf = _surface()
    render.dim_fuel(surf, 2)
    assert _dimmed(surf, 454, 203)
    assert not _dimmed(surf, 454, 205)


def test_fuel_full_lit_no_dim():
    surf = _surface()
    render.dim_fuel(surf, 20)
    assert not _dimmed(surf, 454, 150)


# --- hole punching + warning lights -----------------------------------------

def test_dim_rect_hole_left_undimmed():
    surf = _surface()
    render.dim_rect(surf, (0, 0, 100, 100), holes=[(40, 40, 20, 20)])
    assert not _dimmed(surf, 50, 50)   # inside the hole
    assert _dimmed(surf, 10, 10)       # outside the hole, inside the rect


def test_tach_dim_excludes_check_engine():
    surf = _surface()
    render.dim_tach(surf, 0)           # dim covers x10..403, y16..286
    assert not _dimmed(surf, 376, 255)  # inside check-engine rect → punched out
    assert _dimmed(surf, 340, 255)      # left of the light, still under the tach
    assert _dimmed(surf, 376, 150)      # above the light, still under the tach


def test_dim_check_engine_on_off():
    on = _surface()
    render.dim_check_engine(on, True)
    assert not _dimmed(on, 376, 255)   # lit (fault) → undimmed
    off = _surface()
    render.dim_check_engine(off, False)
    assert _dimmed(off, 376, 255)      # no fault → dimmed


def test_dim_low_fuel_on_off():
    on = _surface()
    render.dim_low_fuel(on, True)
    assert not _dimmed(on, 440, 255)
    off = _surface()
    render.dim_low_fuel(off, False)
    assert _dimmed(off, 440, 255)
