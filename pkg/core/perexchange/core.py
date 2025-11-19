import asyncio

from collections.abc import Sequence

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers import get_scrapers
from perexchange.scrapers.base import ExchangeRateScraper


async def fetch_rates(
    houses: Sequence[str] | None = None,
    *,
    timeout: float = 10.0,
    max_retries: int = 3,
) -> list[ExchangeRate]:
    """
    Fetch current exchange rates from Peruvian exchange houses.

    Args:
        houses: Specific house names to fetch. If None, fetches all.
                Available: cambioseguro, cambiafx, cuantoestaeldolar, instakash,
                           srcambio, tkambio, tucambista, westernunion
        timeout: Request timeout per house (seconds)
        max_retries: Retry attempts for failed requests

    Returns:
        List of ExchangeRate objects. Empty list if all houses fail.

    Example:
        >>> rates = await fetch_rates()
        >>> rates = await fetch_rates(houses=["tkambio", "cambioseguro"])
        >>> best = min(rates, key=lambda r: r.buy_price)
        >>> print(f"Best: {best.name} at S/{best.buy_price}")

    Note:
        Failed houses are silently skipped. Network errors are retried,
        parsing errors fail immediately.
    """
    scrapers = get_scrapers(houses)

    tasks = [_safe_fetch(scraper, timeout, max_retries) for scraper in scrapers]
    results = await asyncio.gather(*tasks)

    return [rate for result in results for rate in result]


async def _safe_fetch(
    scraper: ExchangeRateScraper,
    timeout: float,
    max_retries: int,
) -> list[ExchangeRate]:
    """Fetch from one scraper, return empty list on failure."""
    try:
        return await scraper(timeout=timeout, max_retries=max_retries)
    except (httpx.HTTPError, ValueError):
        return []
