from statistics import mean
from typing import List, Literal, Optional

from .models import ExchangeRate


def find_best_buy(rates: List[ExchangeRate]) -> Optional[ExchangeRate]:
    if not rates:
        return None
    return min(rates, key=lambda r: r.buy_price)


def find_best_sell(rates: List[ExchangeRate]) -> Optional[ExchangeRate]:
    if not rates:
        return None
    return max(rates, key=lambda r: r.sell_price)


def get_top_n(
    rates: List[ExchangeRate], 
    n: int = 3, 
    operation: Literal["buy", "sell"] = "buy"
) -> List[ExchangeRate]:
    if not rates:
        return []

    if operation == "buy":
        sorted_rates = sorted(rates, key=lambda r: r.buy_price)
    else:
        sorted_rates = sorted(rates, key=lambda r: r.sell_price, reverse=True)

    return sorted_rates[:n]


def calculate_average(
    rates: List[ExchangeRate], 
    operation: Literal["buy", "sell"] = "buy"
) -> Optional[float]:
    if not rates:
        return None

    prices = [r.buy_price if operation == "buy" else r.sell_price for r in rates]
    return mean(prices)


def calculate_spread(rates: List[ExchangeRate]) -> Optional[float]:
    if not rates:
        return None
    return mean(r.spread for r in rates)


def filter_by_price_range(
    rates: List[ExchangeRate],
    operation: Literal["buy", "sell"],
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[ExchangeRate]:
    filtered = rates
    price_attr = "buy_price" if operation == "buy" else "sell_price"

    if min_price is not None:
        filtered = [r for r in filtered if getattr(r, price_attr) >= min_price]
    if max_price is not None:
        filtered = [r for r in filtered if getattr(r, price_attr) <= max_price]

    return filtered
