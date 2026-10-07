from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx


async def send(
    client: httpx.AsyncClient, method: str, url: str, **kwargs: Any
) -> httpx.Response:
    """Send one request, turning any failure in the HTTP stack into a transport error.

    A caller-supplied client may use a transport whose errors do not derive from
    `httpx.HTTPError`, such as the `h2` protocol error of an HTTP/2 client. They must
    be retried and reported as a source failure like any other transport error.
    """
    try:
        return await client.request(method, url, **kwargs)
    except httpx.HTTPError:
        raise
    except Exception as error:
        msg = f"{type(error).__name__}: {error}"
        raise httpx.TransportError(msg) from error


@asynccontextmanager
async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create the client shared by one `fetch_rates()` call.

    With HTTP/2, httpcore lets an `h2` protocol error escape when a connection closes
    while a second request waits to initialize it. `send()` turns that error into a
    retryable `httpx.TransportError`.
    """
    async with httpx.AsyncClient(
        http2=True,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        headers={"User-Agent": "perexchange"},
        follow_redirects=True,
        timeout=None,
    ) as client:
        yield client
