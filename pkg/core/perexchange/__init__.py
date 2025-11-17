from .analysis import (
    calculate_average,
    calculate_spread,
    filter_by_price_range,
    find_best_buy,
    find_best_sell,
    get_top_n,
)
from .models import ExchangeRate
from .scrapers import ALL_SCRAPERS, fetch_cuantoestaeldolar


async def fetch_rates(scrapers=None):
    """Fetch rates from all scrapers or specified ones."""
    if scrapers is None:
        scrapers = ALL_SCRAPERS

    all_rates = []
    for scraper_fn in scrapers:
        try:
            rates = await scraper_fn()
            all_rates.extend(rates)
        except Exception:
            continue  # Skip failed scrapers

    return all_rates


__version__ = "1.0.0"

__all__ = [
    "ExchangeRate",
    "fetch_rates",
    "fetch_cuantoestaeldolar",
    "find_best_buy",
    "find_best_sell",
    "get_top_n",
    "calculate_average",
    "calculate_spread",
    "filter_by_price_range",
]
