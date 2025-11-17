from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExchangeRate:
    name: str
    buy_price: float
    sell_price: float
    timestamp: datetime

    @property
    def spread(self) -> float:
        return self.sell_price - self.buy_price

    def __repr__(self) -> str:
        return (
            f"ExchangeRate(name={self.name!r}, "
            f"buy={self.buy_price:.4f}, sell={self.sell_price:.4f})"
        )
