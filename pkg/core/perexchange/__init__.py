import httpx

from perexchange.analysis import find_best_buy, find_best_sell
from perexchange.models import ExchangeRate
from perexchange.scrapers import ALL_SCRAPERS


async def fetch_rates(scrapers=None):
    """
    Fetch exchange rates from all or specified scrapers.

    Failed scrapers are silently skipped to allow partial results.
    Production applications should implement proper error logging.
    """
    if scrapers is None:
        scrapers = ALL_SCRAPERS

    all_rates = []
    for scraper_fn in scrapers:
        try:
            rates = await scraper_fn()
            all_rates.extend(rates)
        except (httpx.HTTPError, ValueError):
            continue

    return all_rates


__version__ = "1.0.0"

__all__ = [
    "ExchangeRate",
    "fetch_rates",
    "find_best_buy",
    "find_best_sell",
]
