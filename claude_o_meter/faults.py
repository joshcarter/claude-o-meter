"""Fault state machine: snapshot → check-engine message (TD-3.8).

Pure (no pygame), so it is unit-testable on its own. The renderer lights the
check-engine light whenever ``fault_message`` is non-None and draws that message
in the bottom status area.

Billing-feed failures (extra-usage / balance) are excluded by construction: the
poller never sets ``stale`` / ``auth_failed`` on those, so they cannot trip a
fault here.

Signals (from poller.py):
  auth_failed            401/403 — cookie needs renewal
  last_update == 0       never polled successfully (startup / poller unreachable)
  stale & last_update>0  had data, now older than STALE_AFTER (or a fetch error)
"""

MSG_NEEDS_AUTH = "NEEDS AUTH"
MSG_NO_DATA = "NO DATA"
MSG_STALE = "DATA STALE"


def fault_message(snapshot):
    """Return the fault message to display, or ``None`` when healthy.

    Priority: needs-auth (most actionable) → no-data (never polled) → stale.
    """
    if snapshot.auth_failed:
        return MSG_NEEDS_AUTH
    if snapshot.last_update == 0:
        return MSG_NO_DATA
    if snapshot.stale:
        return MSG_STALE
    return None
