import asyncio
import math

from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

from perexchange.errors import SourceParseError


T = TypeVar("T")

PARSE_ERRORS = (ValueError, KeyError, TypeError, AttributeError, IndexError)


def _validate_retry_settings(
    max_attempts: object, retry_delay: object
) -> tuple[int, float]:
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
        msg = "max_attempts must be an integer"
        raise TypeError(msg)
    if max_attempts < 1:
        msg = "max_attempts must be at least 1"
        raise ValueError(msg)
    if (
        isinstance(retry_delay, bool)
        or not isinstance(retry_delay, (int, float))
        or retry_delay < 0
        or not math.isfinite(retry_delay)
    ):
        msg = "retry_delay must be a finite, non-negative number"
        raise ValueError(msg)
    return int(max_attempts), float(retry_delay)


def _is_retryable(error: httpx.HTTPError) -> bool:
    """Retry failures that may clear without changing the request."""
    if not isinstance(error, httpx.HTTPStatusError):
        return True
    status = error.response.status_code
    return status in (408, 429) or status >= 500


def _backoff(error: httpx.HTTPError, retry_delay: float, attempt: int) -> float:
    """Return the delay before the next attempt."""
    delay = retry_delay * 2.0**attempt
    if not isinstance(error, httpx.HTTPStatusError):
        return delay
    if error.response.status_code != 429:
        return delay

    retry_after = error.response.headers.get("Retry-After", "")
    try:
        parsed = float(retry_after.strip())
    except ValueError:
        return max(delay, 5.0)
    if not math.isfinite(parsed) or parsed < 0:
        return max(delay, 5.0)
    return min(parsed, 30.0)


async def fetch_with_retry(
    client: httpx.AsyncClient,
    fetch_fn: Callable[[httpx.AsyncClient], Awaitable[T]],
    max_attempts: int,
    retry_delay: float,
    error_context: str,
) -> T:
    """Run one fetch operation with bounded retries and backoff."""
    max_attempts, retry_delay = _validate_retry_settings(max_attempts, retry_delay)
    last_error: httpx.HTTPError | None = None

    for attempt in range(max_attempts):
        try:
            return await fetch_fn(client)
        except httpx.HTTPError as error:
            last_error = error
            if attempt == max_attempts - 1 or not _is_retryable(error):
                break
            await asyncio.sleep(_backoff(error, retry_delay, attempt))
        except PARSE_ERRORS as error:
            msg = (
                f"Failed to parse exchange rates from {error_context}. "
                "The structure may have changed."
            )
            raise SourceParseError(msg) from error

    if last_error is None:
        msg = "Fetch failed without an HTTP error"
        raise SourceParseError(msg)
    raise last_error
