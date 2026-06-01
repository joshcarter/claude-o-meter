"""Tests for the segment-dimming primitive reveal_segments() (TD-3.3).

A solid-colour surface stands in for the (pending) full-on bitmap — the
primitive only needs pixels to dim, not the real art.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from claude_o_meter import layout, render  # noqa: E402

LIT = (200, 200, 200)


def _bar(w, h):
    pygame.init()
    surf = pygame.Surface((w, h))
    surf.fill(LIT)
    return surf


def _is_dimmed(px):
    # Black-over-LIT at any non-zero opacity is strictly darker than LIT.
    return px[0] < LIT[0]


def test_fully_lit_leaves_surface_untouched():
    surf = _bar(200, 40)
    render.reveal_segments(surf, (0, 0, 200, 40), lit=20, total=20)
    assert surf.get_at((0, 0))[:3] == LIT
    assert surf.get_at((199, 39))[:3] == LIT


def test_horizontal_right_pinned_dims_right_half():
    surf = _bar(200, 40)
    render.reveal_segments(surf, (0, 0, 200, 40), lit=10, total=20, orientation="h-right")
    # Left half (lit) untouched; right half (un-lit) dimmed.
    assert surf.get_at((10, 20))[:3] == LIT
    assert surf.get_at((90, 20))[:3] == LIT
    assert _is_dimmed(surf.get_at((110, 20)))
    assert _is_dimmed(surf.get_at((190, 20)))


def test_vertical_top_pinned_dims_top_half():
    surf = _bar(40, 200)
    render.reveal_segments(surf, (0, 0, 40, 200), lit=10, total=20, orientation="v-top")
    # Bottom half (remaining fuel) lit; top half (drained) dimmed.
    assert _is_dimmed(surf.get_at((20, 10)))
    assert _is_dimmed(surf.get_at((20, 90)))
    assert surf.get_at((20, 110))[:3] == LIT
    assert surf.get_at((20, 190))[:3] == LIT


def test_edge_snaps_to_segment_boundary():
    # lit=10.4 rounds to 10 → boundary at x=100 for a 200px / 20-seg bar.
    surf = _bar(200, 40)
    render.reveal_segments(surf, (0, 0, 200, 40), lit=10.4, total=20, orientation="h-right")
    assert surf.get_at((99, 20))[:3] == LIT       # last lit pixel
    assert _is_dimmed(surf.get_at((100, 20)))     # first dimmed pixel


def test_full_opacity_blacks_out_unlit():
    surf = _bar(200, 40)
    render.reveal_segments(surf, (0, 0, 200, 40), lit=0, total=20, opacity=255)
    assert surf.get_at((100, 20))[:3] == (0, 0, 0)


def test_unknown_orientation_raises():
    surf = _bar(200, 40)
    with pytest.raises(ValueError):
        render.reveal_segments(surf, (0, 0, 200, 40), lit=5, total=20, orientation="diagonal")


def test_default_opacity_is_layout_constant():
    a = _bar(200, 40)
    b = _bar(200, 40)
    render.reveal_segments(a, (0, 0, 200, 40), lit=0, total=20)
    render.reveal_segments(b, (0, 0, 200, 40), lit=0, total=20, opacity=layout.DIM_DEFAULT_OPACITY)
    assert a.get_at((100, 20)) == b.get_at((100, 20))
