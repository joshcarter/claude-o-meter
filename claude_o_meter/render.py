"""Pygame renderer for the instrument cluster.

This module owns the drawing. ``render_frame()`` blits the all-segments-lit
cluster bitmap, then dims the un-lit segments of each instrument with a
translucent black rectangle whose edge snaps to a segment boundary:

    TD-3.3  dim_rect()               dimming primitive
    TD-3.4  dim_tach()               tach bar (+ 0–99 readout, pending position)
    TD-3.5  dim_fuel()               vertical fuel gauge
    TD-3.6  low-fuel light           (pending position)
    TD-3.7  money + reset readouts   (pending position)
    TD-3.8  fault state machine → check-engine light + message

Keeping the pure math in ``gauges.py`` (no pygame) means this file is the only
one that imports pygame.
"""

import pygame

from . import assets, gauges, layout

_background = None


def _get_background():
    """Lazily load and cache the all-segments-lit cluster bitmap."""
    global _background
    if _background is None:
        _background = assets.load_image(layout.BACKGROUND)
    return _background


def dim_rect(surface, rect, opacity=None):
    """Blit a translucent black rectangle over ``rect`` (x, y, w, h).

    No-op if the rectangle is empty (w or h ≤ 0), which is how the instrument
    helpers express "fully lit — nothing to dim". ``opacity`` defaults to
    ``layout.DIM_DEFAULT_OPACITY``.
    """
    if opacity is None:
        opacity = layout.DIM_DEFAULT_OPACITY
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, opacity))
    surface.blit(overlay, (x, y))


def dim_tach(surface, lit, opacity=None):
    """Dim the un-lit (right) portion of the tach arc.

    ``lit`` = segments lit (0..TACH_SEGMENTS); fractional values round to a
    whole segment so the dim edge lands on a boundary. The dim rectangle spans
    the full arc height; its left edge = TACH_DIM_LEFT0 + TACH_PITCH·lit.
    """
    lit = max(0, min(layout.TACH_SEGMENTS, int(round(lit))))
    left = layout.TACH_DIM_LEFT0 + layout.TACH_PITCH * lit
    dim_rect(
        surface,
        (left, layout.TACH_DIM_TOP,
         layout.TACH_DIM_RIGHT - left, layout.TACH_DIM_BOTTOM - layout.TACH_DIM_TOP),
        opacity,
    )


def dim_fuel(surface, lit, opacity=None):
    """Dim the un-lit (top) portion of the fuel gauge.

    ``lit`` = segments lit (0..FUEL_SEGMENTS). The dim rectangle is pinned at
    the top; its bottom edge = FUEL_DIM_BOTTOM0 − FUEL_PITCH·lit retreats upward
    as fuel is revealed bottom→top.
    """
    lit = max(0, min(layout.FUEL_SEGMENTS, int(round(lit))))
    bottom = layout.FUEL_DIM_BOTTOM0 - layout.FUEL_PITCH * lit
    dim_rect(
        surface,
        (layout.FUEL_DIM_LEFT, layout.FUEL_DIM_TOP,
         layout.FUEL_DIM_RIGHT - layout.FUEL_DIM_LEFT, bottom - layout.FUEL_DIM_TOP),
        opacity,
    )


def render_frame(surface, snapshot, cfg):
    """Draw one frame of the cluster onto ``surface`` from ``snapshot``.

    Blits the all-segments-lit cluster bitmap, then dims the un-lit tach and
    fuel segments. The numeric readouts and warning lights layer on top in
    TD-3.4/3.6/3.7/3.8 once their positions are specified.
    """
    surface.fill(layout.C_BG)
    surface.blit(_get_background(), (0, 0))
    opacity = cfg.dim_opacity
    dim_tach(surface, gauges.tach_position(snapshot.five_hour_redline_ratio), opacity)
    dim_fuel(surface, gauges.fuel_segments(snapshot.seven_day_pct, layout.FUEL_SEGMENTS), opacity)
    return surface


__all__ = ["render_frame", "dim_rect", "dim_tach", "dim_fuel", "pygame"]
