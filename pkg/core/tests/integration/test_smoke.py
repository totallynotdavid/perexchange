import asyncio

import pytest

from perexchange.scrapers.cambiafx import fetch_cambiafx
from perexchange.scrapers.cambioseguro import fetch_cambioseguro
from perexchange.scrapers.cuantoestaeldolar import fetch_cuantoestaeldolar
from perexchange.scrapers.instakash import fetch_instakash
from perexchange.scrapers.tkambio import fetch_tkambio
from perexchange.scrapers.tucambista import fetch_tucambista
from perexchange.scrapers.westernunion import fetch_westernunion


async def run_with_retry(scraper, house_name, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await scraper(timeout=10.0, max_retries=2)
        except Exception as e:  # noqa: BLE001 (intentional for retry on any error from flaky APIs)
            if attempt == max_attempts - 1:
                pytest.fail(f"{house_name} failed after {max_attempts} attempts: {e}")
            await asyncio.sleep(1)
    return None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scraper,house_name",
    [
        (fetch_cambioseguro, "cambioseguro"),
        (fetch_cambiafx, "cambiafx"),
        (fetch_instakash, "instakash"),
        (fetch_tkambio, "tkambio"),
        (fetch_tucambista, "tucambista"),
        (fetch_westernunion, "westernunion"),
    ],
)
async def test_scraper_returns_valid_data(scraper, house_name):
    rates = await run_with_retry(scraper, house_name)

    assert len(rates) > 0, f"{house_name} returned no rates"
    assert any(house_name in r.name for r in rates)

    for rate in rates:
        assert 2.5 <= rate.buy_price <= 5.0
        assert 2.5 <= rate.sell_price <= 5.0
        assert 0 < rate.spread < 0.5
        assert rate.timestamp is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cuantoestaeldolar_returns_multiple_houses():
    rates = await run_with_retry(fetch_cuantoestaeldolar, "cuantoestaeldolar")

    assert len(rates) >= 5, "cuantoestaeldolar should return multiple houses"

    for rate in rates:
        assert rate.name
        assert 2.5 <= rate.buy_price <= 5.0
        assert 2.5 <= rate.sell_price <= 5.0
        assert 0 < rate.spread < 0.5
