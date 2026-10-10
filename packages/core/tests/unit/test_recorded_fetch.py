"""Fetch sources through `fetch_rates_report()` against recorded responses."""

from datetime import datetime, timezone

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
        ("cambiomundial", datetime(2026, 8, 29, 18, 16, 42, tzinfo=timezone.utc)),
        ("kambioonline", datetime(2026, 8, 29, 18, 0, 15, 366000, tzinfo=timezone.utc)),
        # The market was closed, and the rate dates from the day's start.
        (
            "mercadocambiario",
            datetime(2026, 8, 29, 9, 0, 0, 949000, tzinfo=timezone.utc),
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
    assert rate.timestamp == datetime(2026, 8, 29, 19, 0, 52, tzinfo=timezone.utc)


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
