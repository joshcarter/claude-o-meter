"""Unit tests for poller helpers that don't need the network loop."""

from claude_o_meter.faults import ERR_AUTH, ERR_STALE
from claude_o_meter.poller import STALE_AFTER, _mark_stale_if_aged
from claude_o_meter.state import Snapshot


def test_fresh_data_is_not_stale():
    snap = Snapshot(last_update=1000)
    _mark_stale_if_aged(snap, 1000 + 10)
    assert snap.error is None


def test_aged_data_becomes_stale():
    # The 429-burst case: error is None but the data has aged past STALE_AFTER.
    snap = Snapshot(last_update=1000)
    _mark_stale_if_aged(snap, 1000 + STALE_AFTER + 1)
    assert snap.error == ERR_STALE


def test_never_polled_is_not_marked_stale():
    snap = Snapshot(last_update=0)
    _mark_stale_if_aged(snap, 10**9)
    assert snap.error is None


def test_specific_error_is_not_clobbered():
    snap = Snapshot(error=ERR_AUTH, last_update=1000)
    _mark_stale_if_aged(snap, 1000 + STALE_AFTER + 1)
    assert snap.error == ERR_AUTH
