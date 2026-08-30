import asyncio

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import httpx
import pytest

from perexchange import core
from perexchange.errors import ConfigurationError, SourceError
from perexchange.models import ExchangeRate
from perexchange.scrapers.registry import Source


def rate(source: str, name: str = "house") -> ExchangeRate:
    return ExchangeRate(
        source=source,
        name=name,
        buy_price=3.3,
        sell_price=3.4,
        timestamp=datetime.now(timezone.utc),
    )


async def test_report_keeps_successes_and_describes_source_failures(monkeypatch):
    expected = rate("good")

    good_fetch = AsyncMock(return_value=[expected])
    bad_fetch = AsyncMock(side_effect=SourceError("the source is unavailable"))

    sources = [Source("good", good_fetch), Source("bad", bad_fetch)]
    monkeypatch.setattr(core, "get_sources", lambda source_names: sources)

    async with httpx.AsyncClient() as client:
        report = await core.fetch_rates_report(client=client, total_timeout=None)

    assert report.rates == (expected,)
    assert report.failures[0].source == "bad"
    assert report.failures[0].error_type == "SourceError"
    assert report.failures[0].message == "the source is unavailable"


async def test_aggregator_rates_are_filtered_at_the_core_boundary(monkeypatch):
    fetch_aggregator = AsyncMock(
        return_value=[
            rate("aggregator", "CambiaFX"),
            rate("aggregator", "Uncovered House"),
        ]
    )

    source = Source("aggregator", fetch_aggregator, is_aggregator=True)
    monkeypatch.setattr(core, "get_sources", lambda source_names: [source])

    async with httpx.AsyncClient() as client:
        report = await core.fetch_rates_report(client=client, total_timeout=None)

    assert [item.name for item in report.rates] == ["Uncovered House"]


async def test_rates_are_unique_by_source_and_name(monkeypatch):
    fetch_first = AsyncMock(return_value=[rate("first", "same"), rate("first", "same")])
    fetch_second = AsyncMock(return_value=[rate("second", "same")])

    sources = [Source("first", fetch_first), Source("second", fetch_second)]
    monkeypatch.setattr(core, "get_sources", lambda source_names: sources)

    async with httpx.AsyncClient() as client:
        report = await core.fetch_rates_report(client=client, total_timeout=None)

    assert [(item.source, item.name) for item in report.rates] == [
        ("first", "same"),
        ("second", "same"),
    ]


async def test_total_timeout_is_per_source(monkeypatch):
    async def slow_fetch(client, timeout=10.0, max_attempts=3, retry_delay=0.5):
        await asyncio.sleep(0.05)
        return [rate("slow")]

    source = Source("slow", slow_fetch)
    monkeypatch.setattr(core, "get_sources", lambda source_names: [source])

    async with httpx.AsyncClient() as client:
        report = await core.fetch_rates_report(client=client, total_timeout=0.001)

    assert report.rates == ()
    assert report.failures[0].source == "slow"
    assert report.failures[0].error_type == "TimeoutError"
    assert (
        report.failures[0].message == "source exceeded total timeout of 0.001 seconds"
    )


@pytest.mark.parametrize(
    ("argument", "value"),
    [("timeout", 0), ("max_attempts", 0), ("total_timeout", 0)],
)
async def test_invalid_fetch_settings_raise_configuration_error(argument, value):
    kwargs = {argument: value}

    with pytest.raises(ConfigurationError):
        await core.fetch_rates(sources=[], **kwargs)


async def test_unknown_source_is_rejected_before_fetching():
    with pytest.raises(ConfigurationError, match="Unknown source"):
        await core.fetch_rates(sources=["nonexistent"])


async def test_unexpected_source_errors_propagate(monkeypatch):
    broken_fetch = AsyncMock(side_effect=RuntimeError("programmer error"))

    source = Source("broken", broken_fetch)
    monkeypatch.setattr(core, "get_sources", lambda source_names: [source])

    async with httpx.AsyncClient() as client:
        with pytest.raises(RuntimeError, match="programmer error"):
            await core.fetch_rates_report(client=client, total_timeout=None)


async def test_source_identity_is_checked_at_the_fetch_boundary(monkeypatch):
    wrong_source_fetch = AsyncMock(return_value=[rate("another-source")])

    source = Source("expected-source", wrong_source_fetch)
    monkeypatch.setattr(core, "get_sources", lambda source_names: [source])

    async with httpx.AsyncClient() as client:
        report = await core.fetch_rates_report(client=client, total_timeout=None)

    assert report.rates == ()
    assert report.failures[0].source == "expected-source"
    assert report.failures[0].error_type == "SourceError"
