"""Run the example scripts against captured source responses.

Each source that has a single `URL` answers with its fixture. Every other source answers
`404`, so the scripts also run with failed sources.
"""

import asyncio
import importlib.util

from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

import httpx
import perexchange
import pytest

from perexchange import ExchangeRate

from tests.captured import fixture_client


ROOT = Path(__file__).parents[4]


def load_example(name: str) -> ModuleType:
    path = ROOT / "examples" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"examples_{name}", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def quote(name: str, buy: float, sell: float) -> ExchangeRate:
    return ExchangeRate(
        source=name.split("_", maxsplit=1)[0],
        name=name,
        buy_price=buy,
        sell_price=sell,
        timestamp=datetime.now(timezone.utc),
    )


def test_cheapest_to_buy_is_the_lowest_sell_price():
    rates = [quote("a", 3.30, 3.40), quote("b", 3.20, 3.45), quote("c", 3.35, 3.42)]

    assert load_example("best_rates").cheapest_to_buy(rates).name == "a"


def test_best_to_sell_is_the_highest_buy_price():
    rates = [quote("a", 3.30, 3.40), quote("b", 3.20, 3.45), quote("c", 3.35, 3.42)]

    assert load_example("best_rates").best_to_sell(rates).name == "c"


def test_arbitrage_is_positive_only_when_one_house_pays_more_than_another_charges():
    best_rates = load_example("best_rates")
    overlapping = [quote("a", 3.30, 3.40), quote("b", 3.45, 3.50)]
    consistent = [quote("a", 3.30, 3.40), quote("b", 3.32, 3.38)]

    assert best_rates.arbitrage_per_dollar(overlapping) == pytest.approx(0.05)
    assert best_rates.arbitrage_per_dollar(consistent) < 0


def test_tiers_group_quotes_by_minimum_amount_and_skip_other_variants():
    rates = [
        quote("tk", 3.30, 3.40),
        quote("tk_5000", 3.31, 3.39),
        quote("tk_10000", 3.32, 3.38),
        quote("cs_paralelo", 3.30, 3.40),
        quote("other_5000", 3.33, 3.37),
    ]

    tiers = load_example("best_rates").group_by_tier(rates)

    assert {amount: [r.name for r in group] for amount, group in tiers.items()} == {
        5000: ["tk_5000", "other_5000"],
        10000: ["tk_10000"],
    }


def test_tightest_spreads_come_first():
    rates = [quote("a", 3.30, 3.40), quote("b", 3.35, 3.36), quote("c", 3.30, 3.38)]

    tightest = load_example("market").tightest_spreads(rates, count=2)

    assert [rate.name for rate in tightest] == ["b", "c"]


async def test_best_rates_prints_the_prices_a_customer_gets(capsys):
    async with fixture_client() as client:
        rates = await perexchange.fetch_rates(client=client)
        await load_example("best_rates").main(client)
    output = capsys.readouterr().out

    cheapest = min(rate.sell_price for rate in rates)
    best = max(rate.buy_price for rate in rates)
    assert f"charges S/{cheapest:.4f}" in output
    assert f"pays S/{best:.4f}" in output
    assert "$5000+:" in output
    assert "$comparative" not in output


async def test_market_prints_spreads_and_ranges(capsys):
    async with fixture_client() as client:
        await load_example("market").main(client)
    output = capsys.readouterr().out

    assert "Tightest spreads:" in output
    assert "Houses pay S/3.2000 to" in output
    assert "Houses charge S/" in output


@pytest.mark.parametrize("name", ["best_rates", "market"])
async def test_examples_that_rank_rates_handle_a_fetch_with_no_rates(name, capsys):
    transport = httpx.MockTransport(lambda request: httpx.Response(404))
    async with httpx.AsyncClient(transport=transport) as client:
        await load_example(name).main(client)

    assert capsys.readouterr().out == "No rates available\n"


async def test_basic_lists_rates_and_failed_sources(capsys):
    async with fixture_client() as client:
        await load_example("basic").main(client)
    output = capsys.readouterr().out

    assert "srcambio/srcambio: pays S/3.4300, charges S/3.4520" in output
    assert "Failed westernunion: HTTPStatusError" in output


async def test_cache_fetches_once_inside_the_ttl_and_again_after_it():
    cache_module = load_example("cache")
    now = 0.0
    fetches = 0

    async def fetch() -> list[ExchangeRate]:
        nonlocal fetches
        await asyncio.sleep(0)
        fetches += 1
        return [quote("a", 3.30, 3.40)]

    cache = cache_module.RateCache(fetch=fetch, ttl=60.0, clock=lambda: now)

    await cache.get()
    now = 59.0
    await cache.get()
    assert fetches == 1

    now = 60.0
    await cache.get()
    assert fetches == 2


async def test_cache_example_runs(capsys):
    async with fixture_client() as client:
        await load_example("cache").main(client)

    assert "from the cache: True" in capsys.readouterr().out
