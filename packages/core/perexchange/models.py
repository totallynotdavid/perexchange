from dataclasses import dataclass
from datetime import datetime
from math import isfinite


__all__ = ["ExchangeRate", "FetchReport", "SourceFailure"]


@dataclass(frozen=True, slots=True)
class ExchangeRate:
    """A quoted exchange rate in PEN per USD."""

    source: str
    name: str
    buy_price: float
    sell_price: float
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.source.strip():
            msg = "source must not be empty"
            raise ValueError(msg)
        if not self.name.strip():
            msg = "name must not be empty"
            raise ValueError(msg)
        for field_name, price in (
            ("buy_price", self.buy_price),
            ("sell_price", self.sell_price),
        ):
            _validate_price(field_name, price)
        _validate_timestamp(self.timestamp)

    @property
    def spread(self) -> float:
        """Difference between `sell_price` and `buy_price`, in PEN per USD."""
        return self.sell_price - self.buy_price

    def __str__(self) -> str:
        return (
            f"ExchangeRate(source={self.source!r}, name={self.name!r}, "
            f"buy={self.buy_price:.4f}, sell={self.sell_price:.4f})"
        )


def _validate_price(field_name: str, price: object) -> None:
    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or not isfinite(price)
        or price <= 0
    ):
        msg = f"{field_name} must be a positive finite number"
        raise ValueError(msg)


def _validate_timestamp(timestamp: object) -> None:
    if not isinstance(timestamp, datetime):
        msg = "timestamp must be a datetime"
        raise TypeError(msg)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        msg = "timestamp must be timezone-aware"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class SourceFailure:
    """A source that did not produce rates during a fetch."""

    source: str
    error_type: str
    message: str


@dataclass(frozen=True, slots=True)
class FetchReport:
    """Rates and expected source failures from one fetch."""

    rates: tuple[ExchangeRate, ...]
    failures: tuple[SourceFailure, ...]
