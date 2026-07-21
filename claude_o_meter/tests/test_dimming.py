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


# --- dim_tach: left edge = 14 + 23*lit, spans y 75..287 ---------------------
# Sample at y=220 so we stay clear of the warning-light holes (LF y82–128,
# CE y138–184) that the tach dim punches out on the left edge.
_TY = 220


def test_tach_zero_lit_dims_from_x14():
    surf = _surface()
    render.dim_tach(surf, 0)
    assert _dimmed(surf, 15, _TY)      # inside dim (x≥14)
    assert _dimmed(surf, 465, _TY)     # up to the right edge (466)
    assert not _dimmed(surf, 200, 70)  # above the dim top (75)
    assert not _dimmed(surf, 200, 300)  # below the dim bottom (287)


def test_tach_one_lit_edge_at_x37():
    surf = _surface()
    render.dim_tach(surf, 1)
    assert not _dimmed(surf, 36, _TY)  # revealed (left of edge x=37)
    assert _dimmed(surf, 38, _TY)      # dimmed (right of edge)


def test_tach_two_lit_edge_at_x60():
    surf = _surface()
    render.dim_tach(surf, 2)
    assert not _dimmed(surf, 59, _TY)
    assert _dimmed(surf, 61, _TY)


def test_tach_fractional_rounds_to_boundary():
    a = _surface()
    render.dim_tach(a, 1.4)            # → 1, edge at x=37
    assert not _dimmed(a, 36, _TY) and _dimmed(a, 38, _TY)
    b = _surface()
    render.dim_tach(b, 1.6)            # → 2, edge at x=60
    assert not _dimmed(b, 59, _TY) and _dimmed(b, 61, _TY)


def test_tach_full_lit_no_dim():
    surf = _surface()
    render.dim_tach(surf, 20)
    assert not _dimmed(surf, 200, _TY)


# --- dim_fuel: 25 bars, pitch 5 px, horizontal left→right; dim walks in from right.
# Sampled on the 7-day band [178,25]–[301,37].
_7D = (layout.FUEL_7D_DIM_LEFT, layout.FUEL_7D_DIM_TOP,
       layout.FUEL_7D_DIM_RIGHT, layout.FUEL_7D_DIM_BOTTOM)
_FY = 31  # mid-band y


def _dim_7d(surf, lit):
    render.dim_fuel(surf, lit, *_7D)


def test_fuel_zero_lit_dims_whole_band():
    surf = _surface()
    _dim_7d(surf, 0)
    assert _dimmed(surf, 179, _FY)      # inside dim (x≥178)
    assert _dimmed(surf, 300, _FY)      # up to the right edge (301)
    assert not _dimmed(surf, 240, 24)   # above the band top (25)
    assert not _dimmed(surf, 240, 38)   # below the band bottom (37)
    assert not _dimmed(surf, 177, _FY)  # left of the band (178)
    assert not _dimmed(surf, 302, _FY)  # right of the band (301)


def test_fuel_one_lit_reveals_left_bar():
    # 1 lit → dim left = 178 + 5 = 183; first pitch unit revealed.
    surf = _surface()
    _dim_7d(surf, 1)
    assert not _dimmed(surf, 182, _FY)  # revealed (left of edge x=183)
    assert _dimmed(surf, 184, _FY)      # dimmed (right of edge)


def test_fuel_two_lit_reveals_two_bars():
    # 2 lit → dim left = 178 + 10 = 188.
    surf = _surface()
    _dim_7d(surf, 2)
    assert not _dimmed(surf, 187, _FY)
    assert _dimmed(surf, 189, _FY)


def test_fuel_full_lit_no_dim():
    surf = _surface()
    _dim_7d(surf, 25)
    assert not _dimmed(surf, 240, _FY)


def test_fuel_gauges_are_independent():
    # A gauge only dims its own band: an empty Fable gauge must not touch the
    # 5-hour or 7-day bands to its left.
    surf = _surface()
    render.dim_fuel(surf, 0,
                    layout.FUEL_FABLE_DIM_LEFT, layout.FUEL_FABLE_DIM_TOP,
                    layout.FUEL_FABLE_DIM_RIGHT, layout.FUEL_FABLE_DIM_BOTTOM)
    assert _dimmed(surf, 400, _FY)      # inside the Fable band
    assert not _dimmed(surf, 76, _FY)    # 5-hour band untouched
    assert not _dimmed(surf, 240, _FY)  # 7-day band untouched


# --- hole punching + warning lights -----------------------------------------

def test_dim_rect_hole_left_undimmed():
    surf = _surface()
    render.dim_rect(surf, (0, 0, 100, 100), holes=[(40, 40, 20, 20)])
    assert not _dimmed(surf, 50, 50)   # inside the hole
    assert _dimmed(surf, 10, 10)       # outside the hole, inside the rect


def test_tach_dim_excludes_warning_lights():
    # Both warning lights sit under the tach dim and must be punched out.
    surf = _surface()
    render.dim_tach(surf, 0)           # dim covers x14..466, y75..287
    assert not _dimmed(surf, 37, 161)  # inside check-engine rect → punched out
    assert not _dimmed(surf, 37, 105)  # inside low-fuel rect → punched out
    assert _dimmed(surf, 70, 161)      # right of the lights, still under the tach
    assert _dimmed(surf, 37, 200)      # below check-engine, still under the tach


def test_dim_check_engine_on_off():
    on = _surface()
    render.dim_check_engine(on, True)
    assert not _dimmed(on, 37, 161)   # lit (fault) → undimmed
    off = _surface()
    render.dim_check_engine(off, False)
    assert _dimmed(off, 37, 161)      # no fault → dimmed


def test_dim_low_fuel_on_off():
    # LOW_FUEL_RECT is (13,82,48,46); sample its interior.
    on = _surface()
    render.dim_low_fuel(on, True)
    assert not _dimmed(on, 37, 105)
    off = _surface()
    render.dim_low_fuel(off, False)
    assert _dimmed(off, 37, 105)
