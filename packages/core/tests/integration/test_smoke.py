"""Live checks for the registered scrapers."""

import httpx
import pytest

from perexchange import fetch_rates
from perexchange.scrapers.registry import get_sources, source_for_name


AGGREGATOR = "cuantoestaeldolar"

DIRECT_SOURCES = [
    pytest.param(source.id, source, id=source.id)
    for source in get_sources()
    if source.id != AGGREGATOR
]


async def fetch_live(source, source_name):
    async with httpx.AsyncClient() as client:
        try:
            return await source.fetcher(
                client, timeout=10.0, max_attempts=3, retry_delay=1.0
            )
        except Exception as error:  # ruff: ignore[blind-except]
            pytest.fail(f"{source_name} failed: {error}")


@pytest.mark.integration
@pytest.mark.parametrize(("source_name", "source"), DIRECT_SOURCES)
async def test_scraper_returns_valid_data(source_name, source):
    rates = await fetch_live(source, source_name)

    assert len(rates) > 0, f"{source_name} returned no rates"
    assert any(source_name in rate.name for rate in rates)

    for rate in rates:
        assert 2.5 <= rate.buy_price <= 5.0
        assert 2.5 <= rate.sell_price <= 5.0
        assert 0 < rate.spread < 0.5
        assert rate.timestamp is not None


@pytest.mark.integration
async def test_aggregator_excludes_sources_with_dedicated_scrapers():
    rates = await fetch_rates(sources=[AGGREGATOR])

    for rate in rates:
        assert rate.name
        assert source_for_name(rate.name) is None
        assert 2.5 <= rate.buy_price <= 5.0
        assert 2.5 <= rate.sell_price <= 5.0
        assert 0 < rate.spread < 0.5
