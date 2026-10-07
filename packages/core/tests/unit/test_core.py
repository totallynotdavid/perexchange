import asyncio

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import httpx
import pytest

from perexchange import core
from perexchange.errors import ConfigurationError, SourceError
from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import json_scraper
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


def aggregator_sources(direct):
    """Use an aggregator row that resolves to the selected `cambiafx` source."""
    aggregator = Source(
        "aggregator",
        AsyncMock(
            return_value=[
                rate("aggregator", "CambiaFX"),
                rate("aggregator", "Uncovered House"),
            ]
        ),
        is_aggregator=True,
    )
    return [aggregator, Source("cambiafx", direct)]


async def fetch_with_sources(monkeypatch, sources):
    monkeypatch.setattr(core, "get_sources", lambda source_names: sources)
    async with httpx.AsyncClient() as client:
        return await core.fetch_rates_report(client=client, total_timeout=None)


async def test_aggregator_alone_returns_the_rows_of_every_house(monkeypatch):
    aggregator = aggregator_sources(AsyncMock())[0]

    report = await fetch_with_sources(monkeypatch, [aggregator])

    assert [item.name for item in report.rates] == ["CambiaFX", "Uncovered House"]


async def test_aggregator_row_yields_to_the_selected_source_that_fetched(monkeypatch):
    direct = AsyncMock(return_value=[rate("cambiafx", "cambiafx")])

    report = await fetch_with_sources(monkeypatch, aggregator_sources(direct))

    assert [(item.source, item.name) for item in report.rates] == [
        ("aggregator", "Uncovered House"),
        ("cambiafx", "cambiafx"),
    ]


async def test_aggregator_row_stands_in_for_a_selected_source_that_failed(monkeypatch):
    direct = AsyncMock(side_effect=SourceError("down"))

    report = await fetch_with_sources(monkeypatch, aggregator_sources(direct))

    assert [item.name for item in report.rates] == ["CambiaFX", "Uncovered House"]
    assert [failure.source for failure in report.failures] == ["cambiafx"]


class ProtocolError(Exception):
    """Stands in for `h2.exceptions.ProtocolError`, which is not an `httpx.HTTPError`."""


def break_connection(attempts):
    def handler(request):
        attempts.append(request.url)
        msg = "connection terminated"
        raise ProtocolError(msg)

    return handler


async def test_transport_error_outside_httpx_is_recorded_as_a_source_failure(
    monkeypatch,
):
    attempts = []
    flaky = Source(
        "flaky", json_scraper("flaky", "https://flaky.test/rates", lambda data: [])
    )
    healthy = Source("healthy", AsyncMock(return_value=[rate("healthy")]))
    monkeypatch.setattr(core, "get_sources", lambda source_names: [flaky, healthy])

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(break_connection(attempts))
    ) as client:
        report = await core.fetch_rates_report(
            client=client, max_attempts=2, total_timeout=None
        )

    assert [item.source for item in report.rates] == ["healthy"]
    assert [(f.source, f.error_type) for f in report.failures] == [
        ("flaky", "TransportError")
    ]
    assert "ProtocolError: connection terminated" in report.failures[0].message
    assert len(attempts) == 2


async def test_every_source_records_a_transport_error_outside_httpx():
    attempts = []

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(break_connection(attempts))
    ) as client:
        report = await core.fetch_rates_report(
            client=client, max_attempts=1, total_timeout=None
        )

    assert report.rates == ()
    assert {f.error_type for f in report.failures} == {"TransportError"}
    assert len(report.failures) == len(core.get_sources(None))


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
