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

from . import assets, faults, gauges, layout

_background = None
_font_cache = {}
_cap_offset_cache = {}


def _cap_offset(font):
    """Pixels from a rendered line-box top down to the top of the capitals.

    pygame reserves ascent space above the caps (for accents); a design tool
    measures the visible cap top. Derived from a flat-topped capital so it is a
    font property, independent of the message. Cached per font."""
    off = _cap_offset_cache.get(id(font))
    if off is None:
        off = font.render("H", True, (255, 255, 255)).get_bounding_rect().top
        _cap_offset_cache[id(font)] = off
    return off


def get_font(filename, pt):
    """Cached pygame Font at point size ``pt``. The art is designed at 72 DPI,
    where 1 pt = 1 px, and SDL_ttf sizes in points too, so a point size from the
    Affinity document is passed straight through."""
    key = (filename, pt)
    font = _font_cache.get(key)
    if font is None:
        font = assets.load_font(filename, pt)
        _font_cache[key] = font
    return font


def reset_caches():
    """Drop cached SDL resources (background surface, fonts). Tests call this
    after pygame.quit() so stale handles aren't reused on the next init."""
    global _background
    _background = None
    _font_cache.clear()
    _cap_offset_cache.clear()


def draw_text(surface, text, font, color, *,
              captop_left=None, topleft=None, bottomleft=None, baseline_left=None):
    """Render ``text`` and blit it anchored by the font's metrics (not the
    per-glyph ink), so the position is independent of which characters the
    string contains — every message lands on the same baseline.

      captop_left    top of the visible capitals  (what a design tool measures)
      topleft        line-box top-left            (cap top minus ascent padding)
      bottomleft     line-box bottom-left         (the descender line)
      baseline_left  the typographic baseline

    Returns the line-box Rect placed in surface coordinates.
    """
    glyphs = font.render(text, True, color)
    w, h = glyphs.get_size()
    if captop_left is not None:
        pos = (captop_left[0], captop_left[1] - _cap_offset(font))
    elif topleft is not None:
        pos = topleft
    elif bottomleft is not None:
        pos = (bottomleft[0], bottomleft[1] - h)
    elif baseline_left is not None:
        pos = (baseline_left[0], baseline_left[1] - font.get_ascent())
    else:
        raise ValueError("draw_text needs an anchor "
                         "(captop_left/topleft/bottomleft/baseline_left)")
    surface.blit(glyphs, pos)
    return pygame.Rect(pos[0], pos[1], w, h)


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


def draw_bottom(surface, fault_msg):
    """Bottom status area. Draws the fault message (standard blue) with the top
    of its capitals at BOTTOM_TEXT_POS when one is active. The money readouts
    that occupy this area when healthy are pending their layout spec, so nothing
    is drawn otherwise."""
    if fault_msg:
        font = get_font(layout.FONT_LABEL, layout.BOTTOM_TEXT_PT)
        draw_text(surface, fault_msg, font, layout.C_LIGHT, captop_left=layout.BOTTOM_TEXT_POS)


def render_frame(surface, snapshot, cfg):
    """Draw one frame of the cluster onto ``surface`` from ``snapshot``.

    Blits the all-segments-lit cluster bitmap, dims the un-lit tach/fuel
    segments and the two warning lights, then draws the bottom status area
    (fault message when one is active). The tach 0–99 number and the money
    readouts layer on top once their layouts are specified.
    """
    surface.fill(layout.C_BG)
    surface.blit(_get_background(), (0, 0))
    opacity = cfg.dim_opacity

    dim_tach(surface, gauges.tach_position(snapshot.five_hour_redline_ratio), opacity)
    dim_fuel(surface, gauges.fuel_segments(snapshot.seven_day_pct, layout.FUEL_SEGMENTS), opacity)

    # Low-fuel: lit when 7-day utilisation ≥ 80% (≤ 20% remaining). (TD-3.6)
    low_fuel_on = (snapshot.seven_day_pct or 0.0) >= 80.0
    dim_low_fuel(surface, low_fuel_on, opacity)

    # Check-engine light + bottom message share one fault signal. (TD-3.8)
    fault_msg = faults.fault_message(snapshot)
    dim_check_engine(surface, fault_msg is not None, opacity)
    draw_bottom(surface, fault_msg)

    return surface


__all__ = [
    "render_frame", "dim_rect", "dim_tach", "dim_fuel",
    "dim_check_engine", "dim_low_fuel", "draw_bottom", "draw_text",
    "get_font", "reset_caches", "pygame",
]
