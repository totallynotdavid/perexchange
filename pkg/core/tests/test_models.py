from datetime import UTC, datetime

from perexchange.models import ExchangeRate


def test_exchange_rate_creation():
    timestamp = datetime.now(UTC)
    rate = ExchangeRate("Test House", 3.50, 3.55, timestamp)

    assert rate.name == "Test House"
    assert rate.buy_price == 3.50
    assert rate.sell_price == 3.55
    assert rate.timestamp == timestamp


def test_exchange_rate_spread():
    timestamp = datetime.now(UTC)
    rate = ExchangeRate("Test House", 3.50, 3.55, timestamp)
    assert abs(rate.spread - 0.05) < 1e-10


def test_exchange_rate_repr():
    timestamp = datetime.now(UTC)
    rate = ExchangeRate("Test House", 3.50, 3.55, timestamp)
    repr_str = repr(rate)

    assert "Test House" in repr_str
    assert "3.5000" in repr_str
    assert "3.5500" in repr_str
