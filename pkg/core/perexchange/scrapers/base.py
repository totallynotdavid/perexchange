import asyncio

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Protocol, TypeVar

import httpx

from perexchange.models import ExchangeRate


T = TypeVar("T")


class ExchangeRateScraper(Protocol):
    """Protocol defining the interface all scrapers must implement."""

    def __call__(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> Awaitable[list[ExchangeRate]]:  # fmt: skip
        ...


@asynccontextmanager
async def get_http_client(timeout: float) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Create HTTP client with connection pooling.
    """
    async with httpx.AsyncClient(
        timeout=timeout,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        http2=True,
    ) as client:
        yield client


async def fetch_with_retry(
    fetch_fn: Callable[[httpx.AsyncClient], Awaitable[T]],
    timeout: float,
    max_retries: int,
    retry_delay: float,
    error_context: str,
) -> T:
    """
    Execute fetch function with exponential backoff retry logic.

    Args:
        fetch_fn: Async function that takes an httpx.AsyncClient and returns data
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries (doubles each attempt)
        error_context: URL or context string for error messages

    Returns:
        Result from fetch_fn

    Raises:
        ValueError: On parsing errors (fails immediately, no retry)
        httpx.HTTPError: On network errors after all retries exhausted
    """
    async with get_http_client(timeout) as client:
        last_error = None

        for attempt in range(max_retries):
            try:
                return await fetch_fn(client)

            except httpx.HTTPError as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2**attempt))
                continue

            except (ValueError, KeyError, TypeError, AttributeError, IndexError) as e:
                msg = (
                    f"Failed to parse exchange rates from {error_context}. "
                    "The structure may have changed."
                )
                raise ValueError(msg) from e

        if last_error is None:
            msg = "Failed to fetch rates: no attempts were made"
            raise ValueError(msg)
        raise last_error
