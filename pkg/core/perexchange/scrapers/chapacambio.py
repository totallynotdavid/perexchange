from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://chapacambio.com/wp-json/chapacambio/tasas"


async def fetch_chapacambio(
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch(client: httpx.AsyncClient) -> list[ExchangeRate]:
        response = await client.get(URL)
        response.raise_for_status()
        return _parse_json(response.json())

    return await fetch_with_retry(_fetch, timeout, max_retries, retry_delay, URL)


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
    """Try to create a rate from data, return None if invalid."""
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
