"""Fake data source sweep (TD-3.9): one offline run must exercise every widget —
the tach and fuel gauge sweep their range, the low-fuel light toggles, the money
fields move, and each fault message appears in turn. Verified against the pure
``fake_values`` so it needs no clock and no display."""

from claude_o_meter import faults
from claude_o_meter.fakesource import _FAULTS, CYCLE_SECONDS, fake_values
from claude_o_meter.faults import fault_message
from claude_o_meter.gauges import fuel_segments, tach_number
from claude_o_meter.state import Snapshot

_NOW = 1_700_000_000


def _snapshots(per_cycle=60):
    """Snapshots across enough cycles to rotate through every fault cause."""
    n = per_cycle * len(_FAULTS)
    step = CYCLE_SECONDS / per_cycle
    return [Snapshot(**fake_values(i * step, _NOW)) for i in range(n)]


def test_tach_sweeps_from_zero_to_redline():
    nums = [tach_number(s.five_hour_redline_ratio) for s in _snapshots()]
    assert min(nums) == 0
    assert max(nums) >= 90


def test_fuel_drains_and_crosses_low_threshold():
    snaps = _snapshots()
    segs = [fuel_segments(s.seven_day_pct) for s in snaps]
    assert min(segs) <= 2.0          # near empty
    assert max(segs) >= 18.0         # near full
    # The low-fuel light (7-day utilisation ≥ 80%) both lights and clears.
    low = [(s.seven_day_pct or 0.0) >= 80.0 for s in snaps]
    assert any(low) and not all(low)


def test_money_and_resets_oscillate():
    snaps = _snapshots()
    used = [s.extra_usage_used or 0.0 for s in snaps]
    bal = [s.balance or 0.0 for s in snaps]
    assert max(used) - min(used) > 1.0
    assert max(bal) - min(bal) > 1.0
    # Reset timestamps are populated so the date/time readouts render live, not
    # just their ghosts.
    assert all(s.five_hour_resets_at and s.seven_day_resets_at for s in snaps)


def test_every_fault_message_appears_and_clears():
    msgs = {fault_message(s) for s in _snapshots()}
    assert None in msgs                       # healthy frames → no fault
    assert faults.MSG_NO_DATA in msgs         # the None cause → never-polled
    assert faults.ERR_AUTH in msgs
    assert faults.ERR_CONNECTION in msgs
    assert faults.ERR_STALE in msgs
    assert faults.MSG_WARMING_UP in msgs      # the _WARMING cause → collecting data
