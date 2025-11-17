from statistics import mean
from typing import List, Literal, Optional

from .models import ExchangeRate


def find_best_buy(rates: List[ExchangeRate]) -> Optional[ExchangeRate]:
    """
    Find the best place to buy USD (lowest buy price)
    """
    if not rates:
        return None
    return min(rates, key=lambda r: r.buy_price)


def find_best_sell(rates: List[ExchangeRate]) -> Optional[ExchangeRate]:
    """
    Find the best place to sell USD (highest sell price)
    """
    if not rates:
        return None
    return max(rates, key=lambda r: r.sell_price)


def get_top_n(
    rates: List[ExchangeRate], n: int = 3, operation: Literal["buy", "sell"] = "buy"
) -> List[ExchangeRate]:
    """
    Get top N exchange houses for buying or selling.

    Args:
        rates: List of exchange rates
        n: Number of top exchanges to return
        operation: 'buy' (lowest prices) or 'sell' (highest prices)
    """
    if not rates:
        return []

    if operation == "buy":
        # Sort by buy price ascending (lowest first)
        sorted_rates = sorted(rates, key=lambda r: r.buy_price)
    else:
        # Sort by sell price descending (highest first)
        sorted_rates = sorted(rates, key=lambda r: r.sell_price, reverse=True)

    return sorted_rates[:n]


def calculate_average(
    rates: List[ExchangeRate], operation: Literal["buy", "sell"] = "buy"
) -> Optional[float]:
    """
    Calculate average buy or sell price across all exchange houses.

    Args:
        rates: List of exchange rates
        operation: 'buy' or 'sell'
    """
    if not rates:
        return None

    if operation == "buy":
        prices = [r.buy_price for r in rates]
    else:
        prices = [r.sell_price for r in rates]

    return mean(prices)


def calculate_spread(rates: List[ExchangeRate]) -> Optional[float]:
    """
    Calculate the average spread across all exchange houses.
    The spread is the difference between sell and buy prices.
    """
    if not rates:
        return None

    spreads = [r.spread for r in rates]
    return mean(spreads)


def filter_by_price_range(
    rates: List[ExchangeRate],
    operation: Literal["buy", "sell"],
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[ExchangeRate]:
    """
    Filter exchange rates by price range.

    Args:
        rates: List of exchange rates
        operation: 'buy' or 'sell'
        min_price: Minimum price (inclusive)
        max_price: Maximum price (inclusive)
    """
    filtered = rates

    if operation == "buy":
        if min_price is not None:
            filtered = [r for r in filtered if r.buy_price >= min_price]
        if max_price is not None:
            filtered = [r for r in filtered if r.buy_price <= max_price]
    else:
        if min_price is not None:
            filtered = [r for r in filtered if r.sell_price >= min_price]
        if max_price is not None:
            filtered = [r for r in filtered if r.sell_price <= max_price]

    return filtered
