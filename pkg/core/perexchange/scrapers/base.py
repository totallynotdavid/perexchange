from collections.abc import Awaitable
from typing import Protocol

from perexchange.core import ExchangeRate


class ExchangeRateScraper(Protocol):
    """
    Protocol defining the interface all scrapers must implement.

    All scrapers are async functions with standardized parameters.
    """

    def __call__(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> Awaitable[list[ExchangeRate]]:  # fmt: skip
        ...
