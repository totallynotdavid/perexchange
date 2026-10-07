# ruff: file-ignore[implicit-namespace-package]
"""Reuse fetched rates for a few minutes instead of fetching on every call.

Run from the repository root: `uv run python examples/cache.py`. The script makes live
requests.
"""

import asyncio
import functools
import time

from collections.abc import Awaitable, Callable

import httpx
import perexchange

from perexchange import ExchangeRate


class RateCache:
    def __init__(
        self,
        fetch: Callable[[], Awaitable[list[ExchangeRate]]] = perexchange.fetch_rates,
        ttl: float = 300.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fetch = fetch
        self._ttl = ttl
        self._clock = clock
        self._rates: list[ExchangeRate] = []
        self._fetched_at: float | None = None
        self._lock = asyncio.Lock()

    async def get(self) -> list[ExchangeRate]:
        async with self._lock:
            now = self._clock()
            if self._fetched_at is None or now - self._fetched_at >= self._ttl:
                self._rates = await self._fetch()
                self._fetched_at = now
            return self._rates


async def main(client: httpx.AsyncClient | None = None) -> None:
    cache = RateCache(fetch=functools.partial(perexchange.fetch_rates, client=client))
    first = await cache.get()
    second = await cache.get()
    print(f"First call: {len(first)} rates, fetched")
    print(f"Second call: {len(second)} rates, from the cache: {second is first}")


if __name__ == "__main__":
    asyncio.run(main())
