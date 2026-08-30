from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ExchangeRate:
    """A quoted exchange rate in PEN per USD.

    ``buy_price`` is the amount of PEN needed to buy one USD. ``sell_price`` is
    the amount received for selling one USD.
    """

    name: str
    buy_price: float
    sell_price: float
    timestamp: datetime

    @property
    def spread(self) -> float:
        """Price gap in PEN per USD, calculated as `sell_price - buy_price`."""
        return self.sell_price - self.buy_price

    def __str__(self) -> str:
        return (
            f"ExchangeRate({self.name!r}, "
            f"buy={self.buy_price:.4f}, sell={self.sell_price:.4f})"
        )
