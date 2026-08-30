from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import json_scraper


URL = "https://chapacambio.com/wp-json/chapacambio/tasas"


def _parse_json(response_data: list[dict[str, Any]]) -> list[ExchangeRate]:
    rates = []
    for item in response_data:
        rate = _try_create_rate(item)
        if rate:
            rates.append(rate)

    if not rates:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return rates


def _try_create_rate(data: dict[str, Any]) -> ExchangeRate | None:
    """Return no rate when this entry lacks two positive numeric prices."""
    try:
        buy_price = float(data["MontoCompra"])
        sell_price = float(data["MontoVenta"])
        if buy_price > 0 and sell_price > 0:
            timestamp_str = data.get("updateAt")
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str).replace(
                    tzinfo=timezone.utc
                )
            else:
                timestamp = datetime.now(timezone.utc)
            return ExchangeRate(
                name="chapacambio",
                buy_price=buy_price,
                sell_price=sell_price,
                timestamp=timestamp,
            )
    except (KeyError, ValueError, TypeError):
        pass
    return None


fetch_chapacambio = json_scraper(URL, _parse_json)
