import tempfile
import time

from claude_o_meter.poller import (
    FIVE_HOUR_WINDOW_HOURS,
    _compute_five_hour_burn,
    _window_average_burn,
)
from claude_o_meter.store import Store


def make_store():
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    return Store(f.name)


def test_burn_rate_positive():
    store = make_store()
    now = int(time.time())
    store.insert(now - 1800, 20.0, 50.0, None)
    store.insert(now - 900,  30.0, 55.0, None)
    store.insert(now,        40.0, 60.0, None)

    rate = _compute_five_hour_burn(store)
    assert rate is not None and rate > 0


def test_burn_rate_decaying():
    store = make_store()
    now = int(time.time())
    store.insert(now - 1800, 60.0, 70.0, None)
    store.insert(now,        30.0, 50.0, None)

    assert _compute_five_hour_burn(store) == 0.0


def test_burn_rate_flat():
    store = make_store()
    now = int(time.time())
    store.insert(now - 1800, 50.0, 50.0, None)
    store.insert(now,        50.0, 50.0, None)

    assert _compute_five_hour_burn(store) == 0.0


def test_burn_rate_insufficient_data():
    # A single sample is not enough to compute a slope: None, not a real 0.0.
    store = make_store()
    now = int(time.time())
    store.insert(now, 40.0, 50.0, None)

    assert _compute_five_hour_burn(store) is None


def test_burn_rate_insufficient_span():
    # Two samples a minute apart fall below the 10-minute span guard: None.
    store = make_store()
    now = int(time.time())
    store.insert(now - 60, 40.0, 50.0, None)
    store.insert(now,      41.0, 51.0, None)

    assert _compute_five_hour_burn(store) is None


def test_burn_rate_regression_uses_all_samples():
    # A clean 12 %/hr ramp sampled every minute for 30 minutes.
    store = make_store()
    now = int(time.time())
    for i in range(31):
        store.insert(now - 1800 + i * 60, 0.2 * i, 50.0, None)

    rate = _compute_five_hour_burn(store)
    assert rate is not None and abs(rate - 12.0) < 0.5


def test_burn_rate_regression_resists_endpoint_noise():
    # A flat series with a single high final reading. A two-point slope would
    # report 6 %/hr (3% over 0.5h); the regression keeps it near zero.
    store = make_store()
    now = int(time.time())
    for i in range(30):
        store.insert(now - 1800 + i * 60, 50.0, 50.0, None)
    store.insert(now, 53.0, 50.0, None)

    rate = _compute_five_hour_burn(store)
    assert rate is not None and rate < 2.0


def test_window_average_burn_mid_window():
    # 40% used with 2h remaining of a 5h window → 3h elapsed → 40/3 %/hr.
    now = 1_000_000
    resets_at = now + 2 * 3600
    rate = _window_average_burn(40.0, resets_at, FIVE_HOUR_WINDOW_HOURS, now, 5 / 60)
    assert rate is not None and abs(rate - 40.0 / 3.0) < 1e-6


def test_window_average_burn_too_early():
    # Only 2 minutes into the window — below the 5-minute guard.
    now = 1_000_000
    resets_at = now + int((5.0 - 2 / 60) * 3600)
    assert _window_average_burn(5.0, resets_at, FIVE_HOUR_WINDOW_HOURS, now, 5 / 60) is None


def test_window_average_burn_idle():
    # Zero utilization mid-window is a real 0.0 burn, not unknown.
    now = 1_000_000
    resets_at = now + 2 * 3600
    assert _window_average_burn(0.0, resets_at, FIVE_HOUR_WINDOW_HOURS, now, 5 / 60) == 0.0


def test_provisional_burn_when_no_sample_history():
    # Cold start / empty store: one poll with mid-window util still yields a
    # rough rate so the tach is not stuck at 0 for the first 10 minutes.
    store = make_store()
    now = 1_000_000
    resets_at = now + 2 * 3600  # 3h into the 5h window
    store.insert(now, 30.0, 50.0, None)

    rate = _compute_five_hour_burn(store, pct=30.0, resets_at=resets_at, now=now)
    assert rate is not None and abs(rate - 10.0) < 1e-6  # 30% / 3h


def test_provisional_burn_when_span_too_short():
    # Two samples a minute apart: regression refuses, window average fills in.
    store = make_store()
    now = 1_000_000
    resets_at = now + 2 * 3600
    store.insert(now - 60, 29.0, 50.0, None)
    store.insert(now,      30.0, 50.0, None)

    rate = _compute_five_hour_burn(store, pct=30.0, resets_at=resets_at, now=now)
    assert rate is not None and abs(rate - 10.0) < 1e-6


def test_regression_preferred_over_window_average():
    # Steady recent climb at 12 %/hr; window average would be higher. Once the
    # regression has enough span it must win.
    store = make_store()
    now = 1_000_000
    resets_at = now + 2 * 3600  # window average = 40/3 ≈ 13.3 if pct=40
    for i in range(31):
        store.insert(now - 1800 + i * 60, 0.2 * i, 50.0, None)
    # Current util is 6% after 30 min of 12 %/hr from 0 — but pass a high pct
    # so the average would disagree if it were used.
    rate = _compute_five_hour_burn(store, pct=40.0, resets_at=resets_at, now=now)
    assert rate is not None and abs(rate - 12.0) < 0.5


def test_pre_reset_samples_do_not_poison_slope():
    # Pre-reset samples sit at 90%; post-reset the window climbs 0→12 over 30 min.
    # Without clipping to window start the regression would see a crash and
    # report 0; with clipping it sees the real climb.
    store = make_store()
    now = 1_000_000
    resets_at = now + int(4.5 * 3600)  # window started ~30 min ago
    window_start = resets_at - int(FIVE_HOUR_WINDOW_HOURS * 3600)
    # Old window (before reset): high util.
    store.insert(window_start - 600, 90.0, 50.0, None)
    store.insert(window_start - 60,  92.0, 50.0, None)
    # New window: clean 12 %/hr ramp for 30 minutes.
    for i in range(31):
        store.insert(window_start + i * 60, 0.2 * i, 50.0, None)

    rate = _compute_five_hour_burn(
        store, pct=6.0, resets_at=resets_at, now=window_start + 1800
    )
    assert rate is not None and abs(rate - 12.0) < 0.5
