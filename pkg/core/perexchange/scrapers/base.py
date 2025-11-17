from typing import List, Protocol

from ..models import ExchangeRate


class ExchangeRateScraper(Protocol):
    """
    Protocol defining the interface all scrapers must implement.

    This is not enforced at runtime but serves as documentation
    and enables static type checking.
    """

    async def __call__(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
    ) -> List[ExchangeRate]:  # fmt: skip
        ...
