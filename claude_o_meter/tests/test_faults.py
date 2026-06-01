"""Fault state machine (TD-3.8)."""

from claude_o_meter.faults import (
    MSG_NEEDS_AUTH,
    MSG_NO_DATA,
    MSG_STALE,
    fault_message,
)
from claude_o_meter.state import Snapshot


def test_healthy_has_no_fault():
    assert fault_message(Snapshot(stale=False, last_update=123)) is None


def test_auth_failed_wins():
    # auth_failed also sets stale; needs-auth is the most actionable message.
    snap = Snapshot(auth_failed=True, stale=True, last_update=123)
    assert fault_message(snap) == MSG_NEEDS_AUTH


def test_never_polled_is_no_data():
    assert fault_message(Snapshot(stale=True, last_update=0)) == MSG_NO_DATA


def test_had_data_then_stale():
    assert fault_message(Snapshot(stale=True, last_update=123)) == MSG_STALE
