"""Pygame renderer for the instrument cluster.

This module owns the drawing. TD-3.1 establishes the skeleton: a single
``render_frame()`` entry point that clears the 480×320 surface to the
background colour. The actual widgets land in later sub-TDs and each adds a
helper called from ``render_frame``:

    TD-3.3  reveal_segments()        dimming primitive
    TD-3.4  horizontal tach + 0–99 readout
    TD-3.5  vertical fuel gauge
    TD-3.6  low-fuel light
    TD-3.7  money + reset readouts
    TD-3.8  fault state machine → check-engine light + message

Keeping the pure math in ``gauges.py`` (no pygame) means this file is the only
one that imports pygame.
"""

import pygame

from . import assets, layout

_background = None


def _get_background():
    """Lazily load and cache the all-segments-lit cluster bitmap."""
    global _background
    if _background is None:
        _background = assets.load_image(layout.BACKGROUND)
    return _background


def reveal_segments(surface, rect, lit, total, opacity=None, orientation="h-right"):
    """Reveal ``lit`` of ``total`` segments of an already-blitted full-on bar.

    The caller has already drawn the full-on bitmap into ``rect`` (x, y, w, h).
    This draws a translucent black rectangle over the *un-lit* segments, its
    edge **snapped to a segment boundary**, leaving ``lit`` segments visible.

    ``lit`` may be fractional (e.g. from ``gauges.tach_position``); it is
    rounded to the nearest whole segment so the dim edge always lands on a
    boundary. ``opacity`` defaults to ``layout.DIM_DEFAULT_OPACITY``.

    orientation:
      ``"h-right"`` — horizontal bar, lit fills left→right, dim pinned right.
      ``"v-top"``   — vertical bar, lit fills bottom→top, dim pinned top
                      (drains top→bottom as ``lit`` falls).
    """
    if opacity is None:
        opacity = layout.DIM_DEFAULT_OPACITY
    x, y, w, h = rect
    lit_seg = max(0, min(total, int(round(lit))))
    if lit_seg >= total:
        return  # fully lit — nothing to dim

    if orientation == "h-right":
        seg_w = w / total
        dim_x = x + round(lit_seg * seg_w)
        dim_rect = pygame.Rect(dim_x, y, x + w - dim_x, h)
    elif orientation == "v-top":
        seg_h = h / total
        dim_h = round((total - lit_seg) * seg_h)
        dim_rect = pygame.Rect(x, y, w, dim_h)
    else:
        raise ValueError(f"unknown orientation: {orientation!r}")

    overlay = pygame.Surface((dim_rect.w, dim_rect.h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, opacity))
    surface.blit(overlay, (dim_rect.x, dim_rect.y))


def render_frame(surface, snapshot, cfg):
    """Draw one frame of the cluster onto ``surface`` from ``snapshot``.

    Draws the all-segments-lit cluster bitmap. Per-instrument dimming and the
    text readouts are layered on top by TD-3.4..TD-3.8 (each dims its segments
    via ``reveal_segments`` and blits its readout). ``cfg`` carries display
    knobs (dim opacity, utc offset) those widgets will need.
    """
    surface.fill(layout.C_BG)
    surface.blit(_get_background(), (0, 0))
    # Per-widget dimming + readouts drawn here by TD-3.4..TD-3.8.
    return surface


__all__ = ["render_frame", "pygame"]
