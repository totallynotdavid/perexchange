from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://apis.yanki.pe/api/yanki/v1/tipos-cambio?search=estado:actual"


async def fetch_yanki(
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch(client: httpx.AsyncClient) -> list[ExchangeRate]:
        response = await client.get(URL)
        response.raise_for_status()
        return _parse_json(response.json())

    return await fetch_with_retry(_fetch, timeout, max_retries, retry_delay, URL)


def _parse_json(response_data: dict[str, Any]) -> list[ExchangeRate]:
    rates = []
    data = response_data.get("data", [])

    for item in data:
        rate = _try_create_rate(item)
        if rate:
            rates.append(rate)

    if not rates:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return rates


def _try_create_rate(item: dict[str, Any]) -> ExchangeRate | None:
    """Try to create a rate from item, return None if invalid."""
    try:
        buy_price = float(item["tc_compra"])
        sell_price = float(item["tc_venta"])
        fecha = item["fecha"]
        timestamp = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
        if buy_price > 0 and sell_price > 0:
            return ExchangeRate(
                name="yanki",
                buy_price=buy_price,
                sell_price=sell_price,
                timestamp=timestamp,
            )
    except (KeyError, ValueError, TypeError):
        pass
    return None
