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


def dim_rect(surface, rect, opacity=None, holes=None):
    """Blit a translucent black rectangle over ``rect`` (x, y, w, h).

    ``holes`` is an optional list of (x, y, w, h) rects (in surface coords) to
    leave undimmed — each is punched transparent in the overlay before blitting,
    so an overlapping lit element shows through at full brightness. No-op if the
    rectangle is empty (w or h ≤ 0), which is how the instrument helpers express
    "fully lit — nothing to dim". ``opacity`` defaults to
    ``layout.DIM_DEFAULT_OPACITY``.
    """
    if opacity is None:
        opacity = layout.DIM_DEFAULT_OPACITY
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, opacity))
    for hx, hy, hw, hh in holes or ():
        # Intersect the hole with the dim rect, then punch it transparent in
        # overlay-local coordinates.
        ix, iy = max(x, hx), max(y, hy)
        ax, ay = min(x + w, hx + hw), min(y + h, hy + hh)
        if ax > ix and ay > iy:
            overlay.fill((0, 0, 0, 0), (ix - x, iy - y, ax - ix, ay - iy))
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
        # The check-engine light lives under the arc; never let the tach dim it
        # (it's dimmed by dim_check_engine alone), so it can shine on a fault.
        holes=[layout.CHECK_ENGINE_RECT],
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


def dim_check_engine(surface, on, opacity=None):
    """Dim the check-engine light unless ``on`` (a fault is active)."""
    if not on:
        dim_rect(surface, layout.CHECK_ENGINE_RECT, opacity)


def dim_low_fuel(surface, on, opacity=None):
    """Dim the low-fuel light unless ``on`` (remaining ≤ 20%)."""
    if not on:
        dim_rect(surface, layout.LOW_FUEL_RECT, opacity)


def render_frame(surface, snapshot, cfg):
    """Draw one frame of the cluster onto ``surface`` from ``snapshot``.

    Blits the all-segments-lit cluster bitmap, then dims the un-lit tach and
    fuel segments and the two warning lights when their conditions are not met.
    The numeric readouts layer on top in TD-3.4/3.7 once their positions are
    specified; TD-3.8 will own the full fault → check-engine + message logic.
    """
    surface.fill(layout.C_BG)
    surface.blit(_get_background(), (0, 0))
    opacity = cfg.dim_opacity

    dim_tach(surface, gauges.tach_position(snapshot.five_hour_redline_ratio), opacity)
    dim_fuel(surface, gauges.fuel_segments(snapshot.seven_day_pct, layout.FUEL_SEGMENTS), opacity)

    # Low-fuel: lit when 7-day utilisation ≥ 80% (≤ 20% remaining). (TD-3.6)
    low_fuel_on = (snapshot.seven_day_pct or 0.0) >= 80.0
    dim_low_fuel(surface, low_fuel_on, opacity)

    # Check-engine: interim signal = data stale or auth failed; TD-3.8 refines
    # this into the full fault state machine + message.
    check_engine_on = bool(snapshot.stale or snapshot.auth_failed)
    dim_check_engine(surface, check_engine_on, opacity)

    return surface


__all__ = [
    "render_frame", "dim_rect", "dim_tach", "dim_fuel",
    "dim_check_engine", "dim_low_fuel", "pygame",
]
