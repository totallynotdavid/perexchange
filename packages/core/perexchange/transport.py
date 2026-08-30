from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx


@asynccontextmanager
async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create the client shared by one `fetch_rates()` call."""
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        headers={"User-Agent": "perexchange"},
        follow_redirects=True,
        http2=True,
        timeout=None,
    ) as client:
        yield client
