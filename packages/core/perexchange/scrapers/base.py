from collections.abc import Awaitable
from typing import Protocol

import httpx

from perexchange.models import ExchangeRate


__all__ = ["ExchangeRateScraper"]


class ExchangeRateScraper(Protocol):
    def __call__(
        self,
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_attempts: int = 3,
        retry_delay: float = 0.5,
    ) -> Awaitable[list[ExchangeRate]]: ...
