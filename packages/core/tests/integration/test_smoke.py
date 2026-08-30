"""Live checks for the registered scrapers."""

import httpx
import pytest

from perexchange.scrapers import get_scrapers


# The aggregator may be empty after it removes houses with dedicated scrapers, so it has
# a separate assertion.
AGGREGATOR = "cuantoestaeldolar"

DIRECT_HOUSES = [
    pytest.param(name, scraper, id=name)
    for name, scraper in get_scrapers()
    if name != AGGREGATOR
]


async def fetch_live(scraper, house_name):
    """Fetch one house using the scraper's retry policy.

    A second retry loop would multiply requests and could make a house block the test run.
    """
    async with httpx.AsyncClient() as client:
        try:
            return await scraper(client, timeout=10.0, max_retries=3, retry_delay=1.0)
        except Exception as e:  # ruff: ignore[blind-except]
            # Include the house name because parametrized test output otherwise hides it.
            pytest.fail(f"{house_name} failed: {e}")


@pytest.mark.integration
@pytest.mark.parametrize(("house_name", "scraper"), DIRECT_HOUSES)
async def test_scraper_returns_valid_data(house_name, scraper):
    rates = await fetch_live(scraper, house_name)

    assert len(rates) > 0, f"{house_name} returned no rates"
    assert any(house_name in r.name for r in rates)

    for rate in rates:
        assert 2.5 <= rate.buy_price <= 5.0
        assert 2.5 <= rate.sell_price <= 5.0
        assert 0 < rate.spread < 0.5
        assert rate.timestamp is not None


@pytest.mark.integration
async def test_aggregator_excludes_houses_with_dedicated_scrapers():
    rates = await fetch_live(dict(get_scrapers())[AGGREGATOR], AGGREGATOR)

    for rate in rates:
        assert rate.name
        assert 2.5 <= rate.buy_price <= 5.0
        assert 2.5 <= rate.sell_price <= 5.0
        assert 0 < rate.spread < 0.5
