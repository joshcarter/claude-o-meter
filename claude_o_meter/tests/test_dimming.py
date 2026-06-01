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


# --- dim_fuel: bottom edge = 220 - 8*lit, x 422..456, top 63 ----------------

def test_fuel_zero_lit_dims_to_y220():
    surf = _surface()
    render.dim_fuel(surf, 0)
    assert _dimmed(surf, 439, 64)      # just below top (63)
    assert _dimmed(surf, 439, 219)     # near the bottom (220)
    assert not _dimmed(surf, 439, 62)  # above the dim top
    assert not _dimmed(surf, 420, 150)  # left of the gauge (422)


def test_fuel_one_lit_bottom_at_y212():
    surf = _surface()
    render.dim_fuel(surf, 1)
    assert _dimmed(surf, 439, 211)     # still dimmed above the edge
    assert not _dimmed(surf, 439, 213)  # revealed below the edge (y>212)


def test_fuel_two_lit_bottom_at_y204():
    surf = _surface()
    render.dim_fuel(surf, 2)
    assert _dimmed(surf, 439, 203)
    assert not _dimmed(surf, 439, 205)


def test_fuel_full_lit_no_dim():
    surf = _surface()
    render.dim_fuel(surf, 20)
    assert not _dimmed(surf, 439, 150)
