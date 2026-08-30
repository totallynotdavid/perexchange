import asyncio
import logging

from collections.abc import Sequence

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers import get_scrapers
from perexchange.scrapers.base import ExchangeRateScraper, get_http_client


logger = logging.getLogger("perexchange")


async def fetch_rates(
    houses: Sequence[str] | None = None,
    *,
    timeout: float = 10.0,
    max_retries: int = 3,
    client: httpx.AsyncClient | None = None,
) -> list[ExchangeRate]:
    """Fetch current PEN/USD rates from the selected registered houses.

    An injected client remains owned by the caller; an omitted client is shared
    across this call and closed before the function returns.
    """
    scrapers = get_scrapers(houses)

    if client is not None:
        all_rates = await _fetch_all(scrapers, client, timeout, max_retries)
    else:
        async with get_http_client() as owned_client:
            all_rates = await _fetch_all(scrapers, owned_client, timeout, max_retries)

    seen: dict[str, ExchangeRate] = {}
    for rate in all_rates:
        seen.setdefault(rate.name, rate)

    return list(seen.values())


async def _fetch_all(
    scrapers: list[tuple[str, ExchangeRateScraper]],
    client: httpx.AsyncClient,
    timeout: float,
    max_retries: int,
) -> list[ExchangeRate]:
    tasks = [
        _safe_fetch(house, scraper, client, timeout, max_retries)
        for house, scraper in scrapers
    ]
    results = await asyncio.gather(*tasks)
    return [rate for result in results for rate in result]


async def _safe_fetch(
    house: str,
    scraper: ExchangeRateScraper,
    client: httpx.AsyncClient,
    timeout: float,
    max_retries: int,
) -> list[ExchangeRate]:
    """Return an empty result for an expected source failure."""
    try:
        return await scraper(client, timeout=timeout, max_retries=max_retries)
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("house %s failed: %s", house, e)
        return []
