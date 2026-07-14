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

# Derived: polled fine, but neither the sample regression nor the window-average
# provisional rate is available yet (e.g. brand-new window with no resets_at, or
# too little elapsed time for the average). Shown until a burn estimate exists.
MSG_WARMING_UP = "Collecting Data"


def fault_message(snapshot):
    """Return the fault message to display, or ``None`` when healthy.

    Priority: an explicit error wins; then a never-polled snapshot reads "No
    Data"; then a polled-but-not-enough-history snapshot reads "Collecting
    Data" (the 5h burn rate, hence the tach, isn't trustworthy yet).
    """
    if snapshot.error is not None:
        return snapshot.error
    if snapshot.last_update == 0:
        return MSG_NO_DATA
    if getattr(snapshot, "five_hour_warming_up", False):
        return MSG_WARMING_UP
    return None
