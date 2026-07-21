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


# --- dim_fuel: 15 bars, pitch 3 px, shared column x 423..455, filled bottom→top.
# Sampled on the 7-day band (top 107, bottom 151) at x=440.
_7D_TOP = layout.FUEL_7D_DIM_TOP
_7D_BOT = layout.FUEL_7D_DIM_BOTTOM


def _dim_7d(surf, lit):
    render.dim_fuel(surf, lit, _7D_TOP, _7D_BOT)


def test_fuel_zero_lit_dims_whole_band():
    surf = _surface()
    _dim_7d(surf, 0)
    assert _dimmed(surf, 440, 108)      # just below the band top (107)
    assert _dimmed(surf, 440, 150)      # bottom bar dimmed too
    assert not _dimmed(surf, 440, 106)  # above the band top
    assert not _dimmed(surf, 420, 130)  # left of the column (423)
    assert not _dimmed(surf, 456, 130)  # right of the column (455)


def test_fuel_one_lit_reveals_bottom_bar():
    # 1 lit → dim height = 3*(15-1) = 42, so dim covers 107..148; bottom bar
    # (149,150) is revealed.
    surf = _surface()
    _dim_7d(surf, 1)
    assert _dimmed(surf, 440, 148)      # still dimmed above the edge
    assert not _dimmed(surf, 440, 150)  # revealed bottom bar


def test_fuel_two_lit_reveals_two_bars():
    # 2 lit → dim height 39, covers 107..145; bars at (146,147) and (149,150) lit.
    surf = _surface()
    _dim_7d(surf, 2)
    assert _dimmed(surf, 440, 145)
    assert not _dimmed(surf, 440, 147)


def test_fuel_full_lit_no_dim():
    surf = _surface()
    _dim_7d(surf, 15)
    assert not _dimmed(surf, 440, 130)


def test_fuel_stacked_bands_are_independent():
    # A gauge only dims its own band: an empty Fable gauge must not touch the
    # 5-hour band above it, nor vice-versa.
    surf = _surface()
    render.dim_fuel(surf, 0, layout.FUEL_FABLE_DIM_TOP, layout.FUEL_FABLE_DIM_BOTTOM)
    assert _dimmed(surf, 440, 178)      # inside the Fable band
    assert not _dimmed(surf, 440, 50)   # 5-hour band untouched
    assert not _dimmed(surf, 440, 130)  # 7-day band untouched


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
