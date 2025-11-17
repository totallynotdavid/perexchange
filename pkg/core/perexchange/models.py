from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExchangeRate:
    """
    Exchange rate data for a single exchange house.

    Attributes:
        name: Exchange house name
        buy_price: Price to buy USD (in PEN)
        sell_price: Price to sell USD (in PEN)
        timestamp: When this rate was fetched
    """

    name: str
    buy_price: float
    sell_price: float
    timestamp: datetime

    @property
    def spread(self) -> float:
        """Calculate the spread (sell - buy)."""
        return self.sell_price - self.buy_price

    def __repr__(self) -> str:
        return (
            f"ExchangeRate(name={self.name!r}, "
            f"buy={self.buy_price:.4f}, sell={self.sell_price:.4f})"
        )
