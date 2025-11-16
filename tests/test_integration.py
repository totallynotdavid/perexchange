import pytest

from perexchange.core import ExchangeRate, fetch_rates


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_real_website():
    rates = await fetch_rates()

    assert len(rates) > 0
    assert isinstance(rates, list)
    assert all(isinstance(r, ExchangeRate) for r in rates)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_website_data_quality():
    rates = await fetch_rates()

    assert len(rates) >= 10

    for rate in rates:
        assert rate.name
        assert rate.buy_price > 0
        assert rate.sell_price > 0
        assert 2.5 <= rate.buy_price <= 5.0
        assert 2.5 <= rate.sell_price <= 5.0
        assert rate.spread >= 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_website_no_duplicates():
    rates = await fetch_rates()

    names = [r.name for r in rates]
    unique_names = set(names)

    assert len(names) == len(unique_names)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_website_performance():
    import time

    start = time.time()
    rates = await fetch_rates()
    elapsed = time.time() - start

    assert elapsed < 5.0
    assert len(rates) > 0
