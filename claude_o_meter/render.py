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


def dim_fuel(surface, lit, opacity=None, left=None, right=None):
    """Dim the un-lit (top) portion of a fuel gauge.

    ``lit`` = segments lit (0..FUEL_SEGMENTS). The dim rectangle is pinned at
    the top; its bottom edge = FUEL_DIM_BOTTOM0 − FUEL_PITCH·lit retreats upward
    as fuel is revealed bottom→top. ``left``/``right`` select which gauge column
    to dim, defaulting to the 7-day gauge.
    """
    if left is None:
        left = layout.FUEL_7D_DIM_LEFT
    if right is None:
        right = layout.FUEL_7D_DIM_RIGHT
    lit = max(0, min(layout.FUEL_SEGMENTS, int(round(lit))))
    bottom = layout.FUEL_DIM_BOTTOM0 - layout.FUEL_PITCH * lit
    dim_rect(
        surface,
        (left, layout.FUEL_DIM_TOP, right - left, bottom - layout.FUEL_DIM_TOP),
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
    """Bottom status area when a fault is active: the fault message (standard
    blue) with the top of its capitals at BOTTOM_TEXT_POS. When healthy, this
    area shows the money readouts instead (see ``draw_money``)."""
    if fault_msg:
        font = get_font(layout.FONT_LABEL, layout.BOTTOM_TEXT_PT)
        draw_text(surface, fault_msg, font, layout.C_LIGHT, captop_left=layout.BOTTOM_TEXT_POS)


def _draw_ink_topleft(surface, text, font, color, pos):
    """Blit ``text`` so the top-left of its visible ink lands at ``pos`` — the
    literal corner a design tool reports for a placed text object."""
    glyphs = font.render(text, True, color)
    ink = glyphs.get_bounding_rect()
    surface.blit(glyphs, (pos[0] - ink.x, pos[1] - ink.y))


def draw_money_group(surface, value, label, group, cfg):
    """Draw one money readout group at ``group`` (its top-left): "$", the USD
    value over a dim "888 88" ghost, a ".", and ``label`` — each at its fixed
    offset from the group corner. The value is laid out in uniform digit-width
    cells so the live digits register on the ghost regardless of the (narrower)
    DSEG space advance, and the blank decimal cell aligns under the ".".
    """
    gx, gy = group
    light = layout.C_LIGHT

    f_dollar = get_font(layout.FONT_LABEL, layout.MONEY_DOLLAR_PT)
    _draw_ink_topleft(surface, "$", f_dollar, light,
                      (gx + layout.MONEY_DOLLAR_OFF[0], gy + layout.MONEY_DOLLAR_OFF[1]))

    f_val = get_font(layout.FONT_MONEY, layout.MONEY_VALUE_PT)
    ghost_color = _dim_color(light, cfg.dim_opacity)
    advance = f_val.size("8")[0]                       # DSEG digits are monospaced
    space_w = f_val.size(" ")[0]                        # narrower than a digit
    ink8 = f_val.render("8", True, ghost_color).get_bounding_rect()
    ox = gx + layout.MONEY_VALUE_OFF[0] - ink8.x       # "888 88" ink top-left → offset
    oy = gy + layout.MONEY_VALUE_OFF[1] - ink8.y

    # The field is "DDD CC". Leading dollar blanks must keep a full digit cell so
    # the live digits register on the ghost, but the dollars↔cents gap stays the
    # font's natural space width. So pack the three dollar digits in digit cells,
    # then advance by one real space before the two cent digits.
    def cell_x(i):
        return ox + i * advance if i < 3 else ox + 3 * advance + space_w + (i - 4) * advance

    field = gauges.fmt_money(value)
    for i, ch in enumerate("888 88"):                  # dim all-segments ghost
        if ch != " ":
            surface.blit(f_val.render(ch, True, ghost_color), (cell_x(i), oy))
    for i, ch in enumerate(field):                     # bright live digits over it
        if ch != " ":
            surface.blit(f_val.render(ch, True, light), (cell_x(i), oy))

    f_point = get_font(layout.FONT_LABEL, layout.MONEY_POINT_PT)
    _draw_ink_topleft(surface, ".", f_point, light,
                      (gx + layout.MONEY_POINT_OFF[0], gy + layout.MONEY_POINT_OFF[1]))

    f_label = get_font(layout.FONT_LABEL, layout.MONEY_LABEL_PT)
    _draw_ink_topleft(surface, label, f_label, light,
                      (gx + layout.MONEY_LABEL_OFF[0], gy + layout.MONEY_LABEL_OFF[1]))


def draw_money(surface, snapshot, cfg):
    """Draw the three money readouts (extra / limit / balance) from the
    snapshot. Shown only when there is no active fault."""
    for label, group, field in layout.MONEY_GROUPS:
        draw_money_group(surface, getattr(snapshot, field), label, group, cfg)


def draw_dseg_string(surface, ghost_str, live_str, font, pos, cfg):
    """Draw a fixed-structure DSEG readout: the dim all-segments ``ghost_str``
    with ``live_str`` (same length/structure) bright over it. The ghost's ink
    top-left is anchored at ``pos`` and the live string shares that origin, so
    its digits register on the ghost. ``live_str`` empty → ghost only."""
    ghost_color = _dim_color(layout.C_LIGHT, cfg.dim_opacity)
    ghost = font.render(ghost_str, True, ghost_color)
    ink = ghost.get_bounding_rect()
    origin = (pos[0] - ink.x, pos[1] - ink.y)
    surface.blit(ghost, origin)
    if live_str:
        surface.blit(font.render(live_str, True, layout.C_LIGHT), origin)


def draw_resets(surface, snapshot, cfg):
    """Static labels plus the 7-day reset date and 5-hour reset time readouts,
    each a DSEG value over its dim ghost. Always drawn (top area, independent of
    the fault state); when a timestamp is missing the live string is blank and
    only the ghost shows."""
    light = layout.C_LIGHT
    f_label = get_font(layout.FONT_LABEL, layout.RESET_LABEL_PT)
    f_field = get_font(layout.FONT_MONEY, layout.RESET_FIELD_PT)
    f_dash = get_font(layout.FONT_LABEL, layout.DASH_PT)
    off = cfg.utc_offset_hours

    _draw_ink_topleft(surface, "7 Day Reset", f_label, light, layout.RESET_7D_LABEL_POS)
    draw_dseg_string(surface, layout.DATE_GHOST,
                     gauges.fmt_date(snapshot.seven_day_resets_at, off),
                     f_field, layout.RESET_7D_DATE_POS, cfg)

    _draw_ink_topleft(surface, "5 Hour Reset", f_label, light, layout.RESET_5H_LABEL_POS)
    five = snapshot.five_hour_resets_at
    draw_dseg_string(surface, layout.TIME_GHOST,
                     gauges.fmt_hhmm(five, off) if five else "",
                     f_field, layout.RESET_5H_TIME_POS, cfg)

    _draw_ink_topleft(surface, "-", f_dash, light, layout.DASH_1_POS)
    _draw_ink_topleft(surface, "-", f_dash, light, layout.DASH_2_POS)
    _draw_ink_topleft(surface, "7D", f_label, light, layout.FUEL_7D_LABEL_POS)
    _draw_ink_topleft(surface, "5H", f_label, light, layout.FUEL_5H_LABEL_POS)


def _dim_color(color, opacity):
    """Colour as if a black rectangle at ``opacity`` were blitted over it —
    i.e. brightness scaled by (255 - opacity)/255. Lets the DSEG "88" ghost be
    drawn directly in one dimmed colour instead of a bright draw + a dim box."""
    f = (255 - opacity) / 255.0
    return (round(color[0] * f), round(color[1] * f), round(color[2] * f))


def draw_tach_number(surface, value, cfg):
    """Draw the 0–99 tach readout: a dim "88" ghost (all segments) with the live
    value bright over it, right-aligned in the two-digit field. The visible "88"
    top-left is anchored at NUM_POS."""
    font = get_font(layout.FONT_READOUT, layout.READOUT_SIZE)
    ghost = font.render("88", True, _dim_color(layout.C_LIGHT, cfg.dim_opacity))
    ink = ghost.get_bounding_rect()
    origin = (layout.NUM_POS[0] - ink.x, layout.NUM_POS[1] - ink.y)
    surface.blit(ghost, origin)

    text = str(value)
    advance = font.size("8")[0]           # DSEG digits are monospaced
    live = font.render(text, True, layout.C_LIGHT)
    surface.blit(live, (origin[0] + (2 - len(text)) * advance, origin[1]))


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
    draw_tach_number(surface, gauges.tach_number(snapshot.five_hour_redline_ratio), cfg)
    dim_fuel(surface, gauges.fuel_segments(snapshot.seven_day_pct, layout.FUEL_SEGMENTS),
             opacity, layout.FUEL_7D_DIM_LEFT, layout.FUEL_7D_DIM_RIGHT)
    dim_fuel(surface, gauges.fuel_segments(snapshot.five_hour_pct, layout.FUEL_SEGMENTS),
             opacity, layout.FUEL_5H_DIM_LEFT, layout.FUEL_5H_DIM_RIGHT)

    # Low-fuel: lit when either window drops below 15% remaining (util ≥ 85%). (TD-3.6)
    low_fuel_on = ((snapshot.seven_day_pct or 0.0) >= 85.0
                   or (snapshot.five_hour_pct or 0.0) >= 85.0)
    dim_low_fuel(surface, low_fuel_on, opacity)

    # Reset date/time readouts + static labels (top area, always drawn). (TD-3.7.b)
    draw_resets(surface, snapshot, cfg)

    # Check-engine light + bottom message share one fault signal. (TD-3.8)
    fault_msg = faults.fault_message(snapshot)
    dim_check_engine(surface, fault_msg is not None, opacity)

    # Bottom strip: the fault message when one is active, else money. (TD-3.7)
    if fault_msg:
        draw_bottom(surface, fault_msg)
    else:
        draw_money(surface, snapshot, cfg)

    return surface


__all__ = [
    "render_frame", "dim_rect", "dim_tach", "dim_fuel",
    "dim_check_engine", "dim_low_fuel", "draw_tach_number", "draw_bottom",
    "draw_money", "draw_money_group", "draw_resets", "draw_dseg_string",
    "draw_text", "get_font", "reset_caches", "pygame",
]
