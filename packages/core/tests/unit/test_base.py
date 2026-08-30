import httpx
import pytest

from perexchange.scrapers.base import fetch_with_retry


@pytest.mark.asyncio
async def test_retries_on_network_errors():
    call_count = 0

    def failing_fetch(client):
        nonlocal call_count
        call_count += 1
        msg = "Connection failed"
        raise httpx.HTTPError(msg)

    with pytest.raises(httpx.HTTPError):
        await fetch_with_retry(
            failing_fetch,
            timeout=1.0,
            max_retries=3,
            retry_delay=0.01,
            error_context="test-url",
        )

    assert call_count == 3


@pytest.mark.asyncio
async def test_succeeds_after_transient_failure():
    call_count = 0

    async def sometimes_failing_fetch(client):  # noqa: RUF029 (Must be async to match scraper protocol for awaiting)
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            msg = "Temporary failure"
            raise httpx.HTTPError(msg)
        return "success"

    result = await fetch_with_retry(
        sometimes_failing_fetch,
        timeout=1.0,
        max_retries=3,
        retry_delay=0.01,
        error_context="test-url",
    )

    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_fails_immediately_on_parsing_errors():
    call_count = 0

    def parsing_error_fetch(client):
        nonlocal call_count
        call_count += 1
        msg = "Invalid data"
        raise ValueError(msg)

    with pytest.raises(ValueError, match="Failed to parse exchange rates"):
        await fetch_with_retry(
            parsing_error_fetch,
            timeout=1.0,
            max_retries=3,
            retry_delay=0.01,
            error_context="test-url",
        )

    assert call_count == 1
