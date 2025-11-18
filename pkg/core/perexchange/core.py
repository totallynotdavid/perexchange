import asyncio

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import httpx

from perexchange.scrapers import get_scrapers
from perexchange.scrapers.base import ExchangeRateScraper


@dataclass(frozen=True)
class ExchangeRate:
    """Exchange rate from a single provider."""

    name: str
    buy_price: float  # Price to BUY dollars (sell soles)
    sell_price: float  # Price to SELL dollars (buy soles)
    timestamp: datetime

    @property
    def spread(self) -> float:
        """Difference between buy and sell price."""
        return self.sell_price - self.buy_price

    def __repr__(self) -> str:
        return (
            f"ExchangeRate({self.name!r}, "
            f"buy={self.buy_price:.4f}, sell={self.sell_price:.4f})"
        )


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
                Available: cambioseguro, cuantoestaeldolar, tkambio,
                          tucambista, westernunion
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
