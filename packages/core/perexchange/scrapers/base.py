import asyncio
import re

from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Protocol, TypeVar

import httpx

from perexchange.models import ExchangeRate


T = TypeVar("T")


PARSE_ERRORS = (ValueError, KeyError, TypeError, AttributeError, IndexError)


class ExchangeRateScraper(Protocol):
    def __call__(
        self,
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> Awaitable[list[ExchangeRate]]:  # fmt: skip
        ...


@asynccontextmanager
async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create a client shared by one `fetch_rates()` call.

    Scrapers pass their timeout to each request, so the client has no default timeout.
    """
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        http2=True,
    ) as client:
        yield client


def _is_retryable(error: httpx.HTTPError) -> bool:
    """Retry failures that may clear without changing the request.

    Transport errors, `408`, `429`, and `5xx` responses may be temporary. Other `4xx`
    responses require a change in the request, so retrying them is not useful.
    """
    if not isinstance(error, httpx.HTTPStatusError):
        return True
    status = error.response.status_code
    return status in (408, 429) or status >= 500


def _backoff(error: httpx.HTTPError, retry_delay: float, attempt: int) -> float:
    """Return the next delay, honoring numeric `Retry-After` for `429` responses."""
    delay = retry_delay * 2.0**attempt
    if not isinstance(error, httpx.HTTPStatusError):
        return delay
    if error.response.status_code != 429:
        return delay

    retry_after = error.response.headers.get("Retry-After", "")
    if retry_after.strip().isdigit():
        return min(float(retry_after), 30.0)
    return max(delay, 5.0)


async def fetch_with_retry(
    client: httpx.AsyncClient,
    fetch_fn: Callable[[httpx.AsyncClient], Awaitable[T]],
    max_retries: int,
    retry_delay: float,
    error_context: str,
) -> T:
    """Run one fetch operation with bounded retries and exponential backoff.

    `max_retries` includes the first call. Parsing failures become `ValueError` and stop
    without a retry.
    """
    last_error: httpx.HTTPError | None = None

    for attempt in range(max_retries):
        try:
            return await fetch_fn(client)

        except httpx.HTTPError as e:
            last_error = e
            if attempt == max_retries - 1 or not _is_retryable(e):
                break
            await asyncio.sleep(_backoff(e, retry_delay, attempt))
            continue

        except PARSE_ERRORS as e:
            msg = (
                f"Failed to parse exchange rates from {error_context}. "
                "The structure may have changed."
            )
            raise ValueError(msg) from e

    if last_error is None:
        msg = "Failed to fetch rates: no attempts were made"
        raise ValueError(msg)
    raise last_error


def rate_from_fields(
    data: Mapping[str, Any],
    name: str,
    buy_key: str,
    sell_key: str,
    timestamp: datetime,
) -> ExchangeRate | None:
    """Build a rate when both prices are positive numbers; otherwise return `None`."""
    try:
        buy_price = float(data[buy_key])
        sell_price = float(data[sell_key])
    except (KeyError, ValueError, TypeError):
        return None
    if buy_price <= 0 or sell_price <= 0:
        return None
    return ExchangeRate(
        name=name,
        buy_price=buy_price,
        sell_price=sell_price,
        timestamp=timestamp,
    )


def json_scraper(
    url: str,
    parse: Callable[[Any], list[ExchangeRate]],
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
    data: Mapping[str, str] | None = None,
) -> ExchangeRateScraper:
    async def fetch(
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> list[ExchangeRate]:
        async def _fetch(c: httpx.AsyncClient) -> list[ExchangeRate]:
            response = await c.request(
                method, url, headers=headers, data=data, timeout=timeout
            )
            response.raise_for_status()
            return parse(response.json())

        return await fetch_with_retry(client, _fetch, max_retries, retry_delay, url)

    return fetch


def html_scraper(
    url: str,
    parse: Callable[[str], list[ExchangeRate]],
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
    data: Mapping[str, str] | None = None,
) -> ExchangeRateScraper:
    async def fetch(
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> list[ExchangeRate]:
        async def _fetch(c: httpx.AsyncClient) -> list[ExchangeRate]:
            response = await c.request(
                method, url, headers=headers, data=data, timeout=timeout
            )
            response.raise_for_status()
            return parse(response.text)

        return await fetch_with_retry(client, _fetch, max_retries, retry_delay, url)

    return fetch


def dual_endpoint_json_scraper(
    buy_url: str,
    sell_url: str,
    parse: Callable[[dict[str, Any]], list[ExchangeRate]],
) -> ExchangeRateScraper:
    """Create a scraper for two JSON endpoints with one retry boundary.

    `parse` receives `{"buy": <buy response body>, "sell": <sell response body>}`.
    A retry repeats both endpoint requests.
    """

    async def fetch(
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> list[ExchangeRate]:
        async def _fetch(c: httpx.AsyncClient) -> list[ExchangeRate]:
            buy_response = await c.get(buy_url, timeout=timeout)
            buy_response.raise_for_status()
            sell_response = await c.get(sell_url, timeout=timeout)
            sell_response.raise_for_status()
            return parse({"buy": buy_response.json(), "sell": sell_response.json()})

        return await fetch_with_retry(client, _fetch, max_retries, retry_delay, buy_url)

    return fetch


_CSRF_META = re.compile(r'name="csrf-token"\s+content="([^"]+)"')


def _extract_csrf_token(html_content: str) -> str:
    match = _CSRF_META.search(html_content)
    if not match:
        msg = "Could not find CSRF token on page"
        raise ValueError(msg)
    return match.group(1)


def csrf_convert_scraper(
    base_url: str,
    parse: Callable[[Any], list[ExchangeRate]],
) -> ExchangeRateScraper:
    """Create a scraper for the shared Laravel quote flow.

    The homepage provides a CSRF token. The scraper sends it to `{base_url}convert` for a
    same-origin quote. The page fetch and quote request each have their own retry boundary.
    """
    page_url = base_url
    api_url = f"{base_url}convert"

    async def fetch(
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> list[ExchangeRate]:
        async def _fetch_token(c: httpx.AsyncClient) -> str:
            page_response = await c.get(page_url, timeout=timeout)
            page_response.raise_for_status()
            return _extract_csrf_token(page_response.text)

        token = await fetch_with_retry(
            client, _fetch_token, max_retries, retry_delay, page_url
        )

        async def _fetch_rate(c: httpx.AsyncClient) -> list[ExchangeRate]:
            api_response = await c.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRF-TOKEN": token,
                    "Referer": page_url,
                },
                json={"amount": 1000, "currency": "PEN", "type": "buy", "credits": 0},
                timeout=timeout,
            )
            api_response.raise_for_status()
            return parse(api_response.json())

        return await fetch_with_retry(
            client, _fetch_rate, max_retries, retry_delay, api_url
        )

    return fetch


def rate_from_convert_fields(
    data: Mapping[str, Any], name: str, timestamp: datetime
) -> ExchangeRate | None:
    """Map the platform's sale and buy fields to `ExchangeRate` prices."""
    return rate_from_fields(data, name, "fxBaseSale", "fxBaseBuy", timestamp)
