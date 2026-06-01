"""Pure gauge math, ported verbatim from the PyPortal ``code.py``.

No pygame, no hardware, no I/O — just the numeric mappings the renderer needs.
Keeping these here (rather than in ``render.py``) means they can be unit-tested
without a display and re-used by both the window and framebuffer back-ends.

The tach knobs are the mapping parameters (not pixel layout — that lives in
``layout.py``). They are carried over unchanged from ``code.py`` so the
burn-rate gauge behaves exactly as it did on the PyPortal:

    REDLINE_FRAME   frame/segment for redline_ratio == 1.0 (top of yellow)
    BLUE_EXPONENT   curve below redline; <1 = more sensitive at low use
    RED_FULL_RATIO  redline_ratio that pegs the gauge fully lit
    TACH_FRAMES     position count; tach_position() returns 0.0 .. TACH_FRAMES-1
"""

REDLINE_FRAME = 17
BLUE_EXPONENT = 0.5
RED_FULL_RATIO = 2.0
TACH_FRAMES = 21  # positions 0..20 → lit-segment count for the 20-segment bar


def fmt_hhmm(unix_ts, utc_offset_hours=0):
    """Format a unix timestamp as local HH:MM.

    Ported from ``code.py``; the module-global ``UTC_OFFSET`` is now an explicit
    argument so the function stays pure (default 0 reproduces the old behaviour).
    """
    local = unix_ts + utc_offset_hours * 3600
    h = (local // 3600) % 24
    m = (local // 60) % 60
    return "{:02d}:{:02d}".format(h, m)


def fmt_duration(seconds):
    if seconds <= 0:
        return "--"
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    if h > 0:
        return "~{}h{:02d}m".format(h, m)
    return "~{}m".format(m)


def _clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def tach_position(ratio):
    # 5H redline_ratio -> continuous gauge position, 0.0 .. TACH_FRAMES-1.
    # Concave below the redline (sensitive at low use), linear above it.
    if not ratio or ratio <= 0:
        return 0.0
    if ratio <= 1.0:
        return REDLINE_FRAME * ratio ** BLUE_EXPONENT
    top = TACH_FRAMES - 1
    over = (ratio - 1.0) / (RED_FULL_RATIO - 1.0)
    return min(top, REDLINE_FRAME + (top - REDLINE_FRAME) * over)
