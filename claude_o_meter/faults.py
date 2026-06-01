"""Fault strings + state machine: snapshot → check-engine message (TD-3.8).

Pure (no pygame), so it is unit-testable on its own. The renderer lights the
check-engine light whenever ``fault_message`` is non-None and draws that message
in the bottom status area.

The poller names the cause where it detects it, writing one of the strings below
into ``snapshot.error`` (or ``None`` on a healthy poll). The only state derived
here is "never polled": a snapshot with no error and ``last_update == 0`` has
simply not produced data yet.

Billing-feed failures (extra-usage / balance) are excluded by construction: the
poller never sets ``error`` on those, so they cannot trip a fault here.
"""

# Cause strings written by the poller into ``snapshot.error``.
ERR_NO_TOKEN = "Session token required"  # CLAUDE_SESSION_KEY unset — nothing to send
ERR_AUTH = "Authorization Failed"   # 401/403 — cookie present but rejected
ERR_CONNECTION = "Connection Error"  # request/transport failure
ERR_RESPONSE = "Invalid Response"   # 200 body in an unexpected shape
ERR_STALE = "Data Stale"            # had data, now older than STALE_AFTER

# Derived (no error set, but never polled successfully).
MSG_NO_DATA = "No Data"


def fault_message(snapshot):
    """Return the fault message to display, or ``None`` when healthy.

    An explicit error wins; otherwise a never-polled snapshot reads "No Data".
    """
    if snapshot.error is not None:
        return snapshot.error
    if snapshot.last_update == 0:
        return MSG_NO_DATA
    return None
