from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ExchangeRate:
    name: str
    buy_price: float  # Price to BUY dollars (sell soles)
    sell_price: float  # Price to SELL dollars (buy soles)
    timestamp: datetime

    @property
    def spread(self) -> float:
        """Difference between buy and sell price."""
        return self.sell_price - self.buy_price

    def __repr__(self) -> str:
        return (
            f"ExchangeRate({self.name!r}, "
            f"buy={self.buy_price:.4f}, sell={self.sell_price:.4f})"
        )
