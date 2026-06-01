"""Fault state machine (TD-3.8)."""

from claude_o_meter.faults import (
    ERR_AUTH,
    MSG_NO_DATA,
    MSG_STALE,
    fault_message,
)
from claude_o_meter.state import Snapshot


def test_healthy_has_no_fault():
    assert fault_message(Snapshot(last_update=123)) is None


def test_error_wins_over_no_data():
    # An explicit cause is shown verbatim, even before the first poll lands.
    snap = Snapshot(error=ERR_AUTH, last_update=0)
    assert fault_message(snap) == ERR_AUTH


def test_never_polled_is_no_data():
    assert fault_message(Snapshot(last_update=0)) == MSG_NO_DATA


def test_had_data_then_stale():
    assert fault_message(Snapshot(error=MSG_STALE, last_update=123)) == MSG_STALE
