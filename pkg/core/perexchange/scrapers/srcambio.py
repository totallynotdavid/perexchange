from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://api.srcambio.com/Exchange/Rate?moneda=USD"


async def fetch_srcambio(
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
    official = response_data.get("official", {})
    try:
        buy_price = float(official["buy"])
        sell_price = float(official["sale"])
        return [
            ExchangeRate(
                name="srcambio",
                buy_price=buy_price,
                sell_price=sell_price,
                timestamp=timestamp,
            )
        ]
    except (KeyError, ValueError, TypeError):
        msg = "No valid exchange rates parsed"
        raise ValueError(msg) from None
