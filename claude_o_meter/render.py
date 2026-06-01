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

from . import layout


def render_frame(surface, snapshot, cfg):
    """Draw one frame of the cluster onto ``surface`` from ``snapshot``.

    Skeleton (TD-3.1): clears to the background colour. Widget drawing is added
    by TD-3.3..TD-3.8. ``cfg`` carries display knobs (dim opacity, utc offset)
    those widgets will need.
    """
    surface.fill(layout.C_BG)
    # Widgets drawn here by TD-3.3..TD-3.8.
    return surface


__all__ = ["render_frame", "pygame"]
