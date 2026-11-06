"""Fetch sources through `fetch_rates_report()` against recorded responses."""

import json

from datetime import UTC, datetime

import httpx
import perexchange
import pytest

from tests.captured import fixture_bytes, fixture_client


async def fetch(source: str, client: httpx.AsyncClient) -> perexchange.FetchReport:
    return await perexchange.fetch_rates_report(
        sources=[source], client=client, max_attempts=3
    )


@pytest.mark.parametrize(
    ("source", "recorded_time"),
    [
        # `fecha` has no offset and is Peru time.
        ("cambiomundial", datetime(2026, 8, 29, 18, 16, 42, tzinfo=UTC)),
        ("kambioonline", datetime(2026, 8, 29, 18, 0, 15, 366000, tzinfo=UTC)),
        # The market was closed, and the rate dates from the day's start.
        (
            "mercadocambiario",
            datetime(2026, 8, 29, 9, 0, 0, 949000, tzinfo=UTC),
        ),
    ],
)
async def test_rate_carries_the_time_its_source_published(source, recorded_time):
    async with fixture_client() as client:
        report = await fetch(source, client)

    [rate] = report.rates
    assert rate.timestamp == recorded_time


async def test_okane_rate_carries_the_time_its_source_published():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=fixture_bytes("okane"))
    )
    async with httpx.AsyncClient(transport=transport) as client:
        report = await fetch("okane", client)

    [rate] = report.rates
    assert rate.timestamp == datetime(2026, 8, 29, 19, 0, 52, tzinfo=UTC)


async def test_a_source_that_blocks_this_address_is_reported_with_its_status_once():
    requests: list[httpx.Request] = []

    def refuse(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(403, content=b"Forbidden", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(refuse)) as client:
        report = await fetch("cambiomundial", client)

    assert report.rates == ()
    [failure] = report.failures
    assert (failure.source, failure.error_type, failure.status_code) == (
        "cambiomundial",
        "HTTPStatusError",
        403,
    )
    assert len(requests) == 1, "a refusal is not worth retrying"


async def test_a_source_that_does_not_answer_has_no_status_code():
    def fail(request: httpx.Request) -> httpx.Response:
        msg = "connection refused"
        raise httpx.ConnectError(msg, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(fail)) as client:
        report = await perexchange.fetch_rates_report(
            sources=["cambiomundial"], client=client, max_attempts=1
        )

    [failure] = report.failures
    assert failure.status_code is None


def aggregator_page(*houses: dict[str, object]) -> str:
    row = '"type":"ONLINE-HOUSE"' + json.dumps(list(houses))
    return f"<script>self.__next_f.push({json.dumps([1, row])})</script>"


def house(
    title: str, buy: object = "3.3", sell: object = "3.4", **extra: object
) -> dict[str, object]:
    return {
        "id": title,
        "status": 1,
        "title": title,
        "rates": {"buy": {"cost": buy}, "sale": {"cost": sell}},
        **extra,
    }


@pytest.mark.parametrize(
    "bad_price",
    ["NaN", "Infinity", 10**400],
    ids=["not a number", "infinite", "too large for a float"],
)
async def test_an_aggregator_skips_a_house_with_an_unusable_price(bad_price):
    page = aggregator_page(house("Broken", buy=bad_price), house("Working"))
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=page))

    async with httpx.AsyncClient(transport=transport) as client:
        report = await fetch("cuantoestaeldolar", client)

    assert [rate.name for rate in report.rates] == ["Working"]
    assert report.failures == ()


@pytest.mark.parametrize(
    "stamp",
    [10**30, 10**400],
    ids=["beyond time_t", "beyond float"],
)
async def test_an_aggregator_with_an_impossible_timestamp_still_reports_the_rate(
    stamp,
):
    page = aggregator_page(house("Working", timestamp=stamp))
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=page))

    async with httpx.AsyncClient(transport=transport) as client:
        report = await fetch("cuantoestaeldolar", client)

    [rate] = report.rates
    assert abs(datetime.now(UTC) - rate.timestamp).total_seconds() < 60
