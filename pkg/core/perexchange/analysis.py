from statistics import mean
from typing import Literal

from perexchange.models import ExchangeRate


def find_best_buy(rates: list[ExchangeRate]) -> ExchangeRate | None:
    if not rates:
        return None
    return min(rates, key=lambda r: r.buy_price)


def find_best_sell(rates: list[ExchangeRate]) -> ExchangeRate | None:
    if not rates:
        return None
    return max(rates, key=lambda r: r.sell_price)


def get_top_n(
    rates: list[ExchangeRate],
    n: int = 3,
    operation: Literal["buy", "sell"] = "buy",
) -> list[ExchangeRate]:
    if not rates:
        return []

    if operation == "buy":
        sorted_rates = sorted(rates, key=lambda r: r.buy_price)
    else:
        sorted_rates = sorted(rates, key=lambda r: r.sell_price, reverse=True)

    return sorted_rates[:n]


def calculate_average(
    rates: list[ExchangeRate],
    operation: Literal["buy", "sell"] = "buy",
) -> float | None:
    if not rates:
        return None

    prices = [r.buy_price if operation == "buy" else r.sell_price for r in rates]
    return mean(prices)


def calculate_spread(rates: list[ExchangeRate]) -> float | None:
    if not rates:
        return None
    return mean(r.spread for r in rates)


def filter_by_price_range(
    rates: list[ExchangeRate],
    operation: Literal["buy", "sell"],
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[ExchangeRate]:
    filtered = rates
    price_attr = "buy_price" if operation == "buy" else "sell_price"

    if min_price is not None:
        filtered = [r for r in filtered if getattr(r, price_attr) >= min_price]
    if max_price is not None:
        filtered = [r for r in filtered if getattr(r, price_attr) <= max_price]

    return filtered
