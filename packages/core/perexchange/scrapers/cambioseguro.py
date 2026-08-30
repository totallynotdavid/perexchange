from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://api.cambioseguro.com/api/v1.1/config/rates"


async def fetch_cambioseguro(
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
    timestamp = datetime.now(timezone.utc)
    rates = []
    data = response_data.get("data", {})

    rate_configs = [
        ("cambioseguro", "purchase_price", "sale_price"),
        (
            "cambioseguro_comparative",
            "purchase_price_comparative",
            "sale_price_comparative",
        ),
        ("cambioseguro_paralelo", "purchase_price_paralelo", "sale_price_paralelo"),
    ]

    for name, buy_key, sell_key in rate_configs:
        rate = _try_create_rate(data, name, buy_key, sell_key, timestamp)
        if rate:
            rates.append(rate)

    if not rates:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return rates


def _try_create_rate(
    data: dict[str, Any],
    name: str,
    buy_key: str,
    sell_key: str,
    timestamp: datetime,
) -> ExchangeRate | None:
    """Try to create a rate from data, return None if invalid."""
    try:
        buy_price = float(data[buy_key])
        sell_price = float(data[sell_key])
        if buy_price > 0 and sell_price > 0:
            return ExchangeRate(
                name=name,
                buy_price=buy_price,
                sell_price=sell_price,
                timestamp=timestamp,
            )
    except (KeyError, ValueError, TypeError):
        pass
    return None
