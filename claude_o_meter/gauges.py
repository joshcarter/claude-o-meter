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


def fuel_segments(utilization, segments=20):
    """Remaining-fuel segment position: clamp(100 − utilization, 0, 100) mapped
    linearly onto ``segments``. Returns a float 0..segments (caller rounds to a
    whole segment). ``None`` utilisation is treated as 0 (tank reads full)."""
    if utilization is None:
        utilization = 0.0
    remaining = max(0.0, min(100.0, 100.0 - utilization))
    return remaining / 100.0 * segments


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


def tach_number(ratio):
    """The 0..99 readout value for the tach, from the same redline_ratio as the
    bar (mirrors the PyPortal update_tach: position scaled onto 0..99)."""
    return int(round(tach_position(ratio) / (TACH_FRAMES - 1) * 99))


def fmt_money(value):
    """Format a USD amount as the six-character DSEG field ``"DDD CC"``: three
    dollar digits, a space where the decimal point sits, then two cents digits.

    Leading dollar digits are space-padded (blanked) so they fall on the dim
    "888 88" ghost; cents are always two digits. ``None`` reads as 0.00 and the
    amount is clamped to 999.99 (the field can't show more)."""
    cents = round((value or 0.0) * 100)
    cents = max(0, min(99999, cents))
    return "%3d %02d" % (cents // 100, cents % 100)
