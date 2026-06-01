"""Unit tests for the pure gauge math ported from the PyPortal code.py (TD-3.2)."""

from claude_o_meter.gauges import (
    REDLINE_FRAME,
    RED_FULL_RATIO,
    TACH_FRAMES,
    _clamp01,
    fmt_duration,
    fmt_hhmm,
    tach_position,
)


def test_fmt_hhmm_utc():
    # 2026-06-01 12:34:00 UTC = 1780662840
    assert fmt_hhmm(1780662840) == "12:34"


def test_fmt_hhmm_offset_wraps_day():
    # 23:00 UTC shifted by +2h wraps forward past midnight to 01:00.
    eleven_pm_utc = 1780614000  # 2026-06-01 23:00:00 UTC
    assert fmt_hhmm(eleven_pm_utc) == "23:00"
    assert fmt_hhmm(eleven_pm_utc, utc_offset_hours=2) == "01:00"
    assert fmt_hhmm(eleven_pm_utc, utc_offset_hours=-7) == "16:00"


def test_fmt_duration():
    assert fmt_duration(0) == "--"
    assert fmt_duration(-5) == "--"
    assert fmt_duration(90) == "~1m"
    assert fmt_duration(3600) == "~1h00m"
    assert fmt_duration(3600 + 23 * 60) == "~1h23m"


def test_clamp01():
    assert _clamp01(-0.5) == 0.0
    assert _clamp01(0.0) == 0.0
    assert _clamp01(0.37) == 0.37
    assert _clamp01(1.0) == 1.0
    assert _clamp01(2.5) == 1.0


def test_tach_position_zero_and_none():
    assert tach_position(0) == 0.0
    assert tach_position(None) == 0.0
    assert tach_position(-1.0) == 0.0


def test_tach_position_redline_hits_redline_frame():
    # ratio == 1.0 → exactly REDLINE_FRAME (1.0 ** anything == 1.0).
    assert tach_position(1.0) == REDLINE_FRAME


def test_tach_position_concave_below_redline():
    # BLUE_EXPONENT < 1 means a quarter of the burn lights more than a quarter
    # of the way to redline (sensitive at low use).
    assert tach_position(0.25) > REDLINE_FRAME * 0.25


def test_tach_position_pegs_at_full_ratio():
    top = TACH_FRAMES - 1
    assert tach_position(RED_FULL_RATIO) == top
    # Beyond RED_FULL_RATIO it stays pinned at the top, never overshoots.
    assert tach_position(RED_FULL_RATIO * 3) == top


def test_tach_position_monotonic():
    prev = -1.0
    for r in [0.1, 0.5, 1.0, 1.5, 2.0]:
        cur = tach_position(r)
        assert cur >= prev
        prev = cur
