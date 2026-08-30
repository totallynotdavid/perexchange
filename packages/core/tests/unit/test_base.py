import httpx
import pytest

from perexchange.scrapers.base import _backoff, fetch_with_retry


@pytest.mark.asyncio
async def test_retries_on_network_errors():
    call_count = 0

    def failing_fetch(client):
        nonlocal call_count
        call_count += 1
        msg = "Connection failed"
        raise httpx.HTTPError(msg)

    async with httpx.AsyncClient() as client:
        with pytest.raises(httpx.HTTPError):
            await fetch_with_retry(
                client,
                failing_fetch,
                max_retries=3,
                retry_delay=0.01,
                error_context="test-url",
            )

    assert call_count == 3


@pytest.mark.asyncio
async def test_succeeds_after_transient_failure():
    call_count = 0

    async def sometimes_failing_fetch(client):  # ruff: ignore[unused-async] (matches scraper protocol)
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            msg = "Temporary failure"
            raise httpx.HTTPError(msg)
        return "success"

    async with httpx.AsyncClient() as client:
        result = await fetch_with_retry(
            client,
            sometimes_failing_fetch,
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

    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match="Failed to parse exchange rates"):
            await fetch_with_retry(
                client,
                parsing_error_fetch,
                max_retries=3,
                retry_delay=0.01,
                error_context="test-url",
            )

    assert call_count == 1


def status_error(status_code, headers=None):
    request = httpx.Request("GET", "https://example.test/rates")
    response = httpx.Response(status_code, headers=headers or {}, request=request)
    return httpx.HTTPStatusError("boom", request=request, response=response)


async def count_attempts(error, max_retries=3, retry_delay=0.01):
    attempts = 0

    def always_failing(client):
        nonlocal attempts
        attempts += 1
        raise error

    async with httpx.AsyncClient() as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_with_retry(
                client,
                always_failing,
                max_retries=max_retries,
                retry_delay=retry_delay,
                error_context="test-url",
            )
    return attempts


@pytest.mark.parametrize("status", [400, 403, 404])
async def test_client_errors_are_not_retried(status):
    assert await count_attempts(status_error(status)) == 1


@pytest.mark.parametrize("status", [408, 429, 500, 503])
async def test_transient_errors_are_retried(status):
    assert await count_attempts(status_error(status)) == 3


def test_rate_limit_backoff_honours_retry_after():
    error = status_error(429, headers={"Retry-After": "7"})

    assert _backoff(error, retry_delay=0.5, attempt=0) == pytest.approx(7.0)


def test_rate_limit_backoff_caps_absurd_retry_after():
    error = status_error(429, headers={"Retry-After": "3600"})

    assert _backoff(error, retry_delay=0.5, attempt=0) == pytest.approx(30.0)


def test_rate_limit_without_retry_after_waits_longer_than_normal():
    plain = status_error(503)
    limited = status_error(429)

    assert _backoff(limited, retry_delay=0.5, attempt=0) > _backoff(
        plain, retry_delay=0.5, attempt=0
    )
