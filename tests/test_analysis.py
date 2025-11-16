from datetime import UTC, datetime

import pytest

from perexchange.core import (
    ExchangeRate,
    find_best_buy,
    find_best_sell,
    get_top_n,
)


@pytest.fixture
def sample_rates():
    timestamp = datetime.now(UTC)
    return [
        ExchangeRate("House A", 3.30, 3.35, timestamp),
        ExchangeRate("House B", 3.35, 3.42, timestamp),
        ExchangeRate("House C", 3.32, 3.45, timestamp),
        ExchangeRate("House D", 3.40, 3.41, timestamp),
        ExchangeRate("House E", 3.33, 3.40, timestamp),
    ]


def test_find_best_buy(sample_rates):
    best = find_best_buy(sample_rates)
    assert best.name == "House A"
    assert best.buy_price == 3.30


def test_find_best_sell(sample_rates):
    best = find_best_sell(sample_rates)
    assert best.name == "House C"
    assert best.sell_price == 3.45


def test_get_top_buy(sample_rates):
    top_3 = get_top_n(sample_rates, n=3, operation="buy")
    assert len(top_3) == 3
    assert top_3[0].name == "House A"
    assert top_3[1].name == "House C"
    assert top_3[2].name == "House E"
