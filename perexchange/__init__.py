from .core import (
    ExchangeRate,
    calculate_average,
    calculate_spread,
    fetch_rates,
    find_best_buy,
    find_best_sell,
    get_top_n,
)

__version__ = "1.0.0"

__all__ = [
    "ExchangeRate",
    "fetch_rates",
    "find_best_buy",
    "find_best_sell",
    "get_top_n",
    "calculate_average",
    "calculate_spread",
]
