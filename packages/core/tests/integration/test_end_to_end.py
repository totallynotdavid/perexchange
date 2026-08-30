import asyncio

import pytest

from perexchange import fetch_rates


async def run_with_retry(max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await fetch_rates(timeout=10.0, max_retries=2)
        except Exception as e:  # noqa: BLE001 (intentional for retry on any error from flaky APIs)
            if attempt == max_attempts - 1:
                pytest.fail(f"fetch_rates failed after {max_attempts} attempts: {e}")
            await asyncio.sleep(1)
    return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_all_houses():
    rates = await run_with_retry()

    assert len(rates) >= 10, "Expected at least 10 total rates"

    names = {r.name for r in rates}
    core_houses = {"cambioseguro", "tkambio", "tucambista", "westernunion"}

    missing = core_houses - names
    if missing:
        pytest.skip(f"Core houses unavailable: {missing}")

    for rate in rates:
        assert rate.name
        assert 2.5 <= rate.buy_price <= 5.0, f"{rate.name} buy price out of range"
        assert 2.5 <= rate.sell_price <= 5.0, f"{rate.name} sell price out of range"
        assert 0 < rate.spread < 0.5, f"{rate.name} spread suspicious"
        assert rate.timestamp is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_no_duplicate_rates():
    rates = await run_with_retry()
    names = [r.name for r in rates]

    assert len(names) == len(set(names)), f"Duplicate rates found: {names}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_performance():
    import time

    start = time.time()
    rates = await run_with_retry()
    elapsed = time.time() - start

    assert elapsed < 8.0, f"Fetching took {elapsed:.2f}s (expected < 8s)"
    assert len(rates) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_specific_houses():
    rates = await fetch_rates(houses=["tkambio", "tucambista"])

    names = {r.name for r in rates}
    assert any("tkambio" in name for name in names)
    assert any("tucambista" in name for name in names)

    unwanted = names - {n for n in names if "tkambio" in n or "tucambista" in n}
    assert not unwanted, f"Got rates from non-requested houses: {unwanted}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_house_name():
    with pytest.raises(ValueError, match="Unknown house"):
        await fetch_rates(houses=["nonexistent"])
