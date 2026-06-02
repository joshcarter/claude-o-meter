"""Unit tests for poller helpers that don't need the network loop."""

from claude_o_meter.faults import ERR_AUTH, ERR_STALE
from claude_o_meter.poller import STALE_AFTER, _iso_to_unix, _mark_stale_if_aged
from claude_o_meter.state import Snapshot


def test_iso_to_unix_null_returns_none():
    """The API sends resets_at=null for an idle window; that must parse to None,
    not raise (the AttributeError was being mis-shown as 'Connection Error')."""
    assert _iso_to_unix(None) is None


def test_iso_to_unix_parses_all_forms_to_same_instant():
    # Z-suffix, bare-naive (assumed UTC), and an explicit offset all name 2026-03-01T12:00:00Z.
    z = _iso_to_unix("2026-03-01T12:00:00Z")
    naive = _iso_to_unix("2026-03-01T12:00:00")
    offset = _iso_to_unix("2026-03-01T17:30:00+05:30")
    assert z == naive == offset


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
