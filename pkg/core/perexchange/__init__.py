from collections.abc import Sequence

import httpx

from perexchange.analysis import find_best_buy, find_best_sell
from perexchange.models import ExchangeRate
from perexchange.scrapers import ALL_SCRAPERS
from perexchange.scrapers.base import ExchangeRateScraper


async def fetch_rates(
    scrapers: Sequence[ExchangeRateScraper] | None = None,
) -> list[ExchangeRate]:
    """
    Fetch exchange rates from all or specified scrapers.

    Failed scrapers are silently skipped to allow partial results.
    Production applications should implement proper error logging.
    """
    scrapers_to_use: Sequence[ExchangeRateScraper] = (
        scrapers if scrapers is not None else ALL_SCRAPERS
    )

    all_rates: list[ExchangeRate] = []
    for scraper_fn in scrapers_to_use:
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
