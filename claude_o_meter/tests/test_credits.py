"""Unit tests for cents→USD parsing and currency guard (TD-12.4)."""

from claude_o_meter.poller import _parse_cents_usd, _currency_ok


def test_cents_to_usd_basic():
    assert _parse_cents_usd(2000) == 20.0


def test_cents_to_usd_fractional():
    assert _parse_cents_usd(12000) == 120.0


def test_cents_to_usd_zero():
    assert _parse_cents_usd(0) == 0.0
    assert _parse_cents_usd(0.0) == 0.0


def test_cents_to_usd_none():
    assert _parse_cents_usd(None) is None


def test_cents_to_usd_float_input():
    # used_credits comes as float in the API (e.g. 0.0)
    result = _parse_cents_usd(150.0)
    assert result is not None
    assert abs(result - 1.5) < 1e-9


def test_currency_ok_usd():
    assert _currency_ok("USD", "test") is True


def test_currency_ok_none():
    # absent currency field treated as OK
    assert _currency_ok(None, "test") is True


def test_currency_ok_non_usd():
    assert _currency_ok("EUR", "test_eur_guard") is False
