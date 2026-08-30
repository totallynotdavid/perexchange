from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ExchangeRate:
    """A quoted exchange rate in PEN per USD.

    `buy_price` is the PEN needed to buy one USD. `sell_price` is the PEN received for
    selling one USD.
    """

    name: str
    buy_price: float
    sell_price: float
    timestamp: datetime

    @property
    def spread(self) -> float:
        """Difference between `sell_price` and `buy_price`, in PEN per USD."""
        return self.sell_price - self.buy_price

    def __str__(self) -> str:
        return (
            f"ExchangeRate({self.name!r}, "
            f"buy={self.buy_price:.4f}, sell={self.sell_price:.4f})"
        )
