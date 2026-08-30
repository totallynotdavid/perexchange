"""Live checks for one shared `fetch_rates()` call."""

import asyncio
import time

from dataclasses import dataclass

import pytest

from perexchange import fetch_rates
from perexchange.models import ExchangeRate


@dataclass(frozen=True)
class Fanout:
    rates: list[ExchangeRate]
    elapsed: float


@pytest.fixture(scope="session")
def fanout() -> Fanout:
    start = time.monotonic()
    rates = asyncio.run(fetch_rates(timeout=10.0, max_retries=3))
    return Fanout(rates=rates, elapsed=time.monotonic() - start)


@pytest.mark.integration
def test_returns_well_formed_rates_from_most_houses(fanout):
    assert len(fanout.rates) >= 10, "Expected at least 10 total rates"

    for rate in fanout.rates:
        assert rate.name
        assert 2.5 <= rate.buy_price <= 5.0, f"{rate.name} buy price out of range"
        assert 2.5 <= rate.sell_price <= 5.0, f"{rate.name} sell price out of range"
        assert 0 < rate.spread < 0.5, f"{rate.name} spread suspicious"
        assert rate.timestamp is not None


@pytest.mark.integration
def test_no_duplicate_rates(fanout):
    names = [r.name for r in fanout.rates]

    assert len(names) == len(set(names)), f"Duplicate rates found: {names}"


@pytest.mark.integration
def test_houses_are_fetched_concurrently(fanout):
    # Keep the bound loose for slow endpoints, but below a serial fetch of all houses.
    assert fanout.elapsed < 8.0, f"Fetching took {fanout.elapsed:.2f}s (expected < 8s)"


@pytest.mark.integration
async def test_fetch_specific_houses():
    rates = await fetch_rates(houses=["tkambio", "tucambista"])

    names = {r.name for r in rates}
    assert any("tkambio" in name for name in names)
    assert any("tucambista" in name for name in names)

    unwanted = names - {n for n in names if "tkambio" in n or "tucambista" in n}
    assert not unwanted, f"Got rates from non-requested houses: {unwanted}"


async def test_invalid_house_name():
    with pytest.raises(ValueError, match="Unknown house"):
        await fetch_rates(houses=["nonexistent"])
