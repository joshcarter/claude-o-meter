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
    segs = [fuel_segments(s.seven_day_pct) for s in snaps]  # 25-bar gauge
    assert min(segs) <= 2.0          # near empty
    assert max(segs) >= 20.0         # near full (7d util bottoms out ~5%)
    # The low-fuel light (any window's utilisation ≥ 85%) both lights and clears.
    low = [(s.seven_day_pct or 0.0) >= 85.0
           or (s.five_hour_pct or 0.0) >= 85.0
           or (s.fable_pct or 0.0) >= 85.0
           for s in snaps]
    assert any(low) and not all(low)


def test_fable_gauge_sweeps():
    # The offline demo must exercise the third gauge too, crossing the low-fuel
    # threshold so its warning contribution is seen.
    snaps = _snapshots()
    segs = [fuel_segments(s.fable_pct) for s in snaps]
    assert min(segs) <= 3.0          # near empty on a 25-bar gauge
    assert max(segs) >= 20.0
    assert any((s.fable_pct or 0.0) >= 85.0 for s in snaps)


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


def test_warming_state_matches_real_poller_contract():
    """While warming, the real poller leaves five_hour_burn_rate AND
    five_hour_redline_ratio None (too little history for a slope). The fake must
    produce the same shape, or renderers tested offline take a path the live
    source never emits."""
    warming = [s for s in _snapshots() if s.five_hour_warming_up]
    assert warming, "the sweep never reaches the warming state"
    for s in warming:
        assert s.five_hour_burn_rate is None
        assert s.five_hour_redline_ratio is None
