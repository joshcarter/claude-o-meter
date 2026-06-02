"""Fault state machine (TD-3.8)."""

from claude_o_meter.faults import (
    ERR_AUTH,
    ERR_STALE,
    MSG_NO_DATA,
    MSG_WARMING_UP,
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
    assert fault_message(Snapshot(error=ERR_STALE, last_update=123)) == ERR_STALE


def test_warming_up_when_polled_without_enough_history():
    # Polled OK, but the 5h burn rate isn't trustworthy yet.
    snap = Snapshot(last_update=123, five_hour_warming_up=True)
    assert fault_message(snap) == MSG_WARMING_UP


def test_error_wins_over_warming_up():
    snap = Snapshot(error=ERR_AUTH, last_update=123, five_hour_warming_up=True)
    assert fault_message(snap) == ERR_AUTH


def test_no_data_wins_over_warming_up():
    snap = Snapshot(last_update=0, five_hour_warming_up=True)
    assert fault_message(snap) == MSG_NO_DATA
