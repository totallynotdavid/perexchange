from datetime import datetime, timezone

import pytest

from perexchange.models import ExchangeRate


def valid_rate(**overrides) -> ExchangeRate:
    values = {
        "source": "cambiafx",
        "name": "CambiaFX",
        "buy_price": 3.3,
        "sell_price": 3.4,
        "timestamp": datetime.now(timezone.utc),
    }
    values.update(overrides)
    return ExchangeRate(**values)


def test_exchange_rate_is_an_immutable_value_object():
    rate = valid_rate()

    with pytest.raises(AttributeError):
        rate.name = "other"


@pytest.mark.parametrize("field", ["source", "name"])
def test_source_and_name_must_not_be_empty(field):
    with pytest.raises(ValueError, match="must not be empty"):
        valid_rate(**{field: "   "})


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
@pytest.mark.parametrize("field", ["buy_price", "sell_price"])
def test_prices_must_be_positive_and_finite(field, value):
    with pytest.raises(ValueError, match="positive finite number"):
        valid_rate(**{field: value})


def test_timestamp_must_be_timezone_aware():
    with pytest.raises(ValueError, match="timezone-aware"):
        valid_rate(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc).replace(tzinfo=None)
        )


def test_timestamp_must_be_a_datetime():
    with pytest.raises(TypeError, match="must be a datetime"):
        valid_rate(timestamp="2026-01-01")
