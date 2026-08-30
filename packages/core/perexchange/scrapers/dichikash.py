from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


# Buy and sell rates come from two independent endpoints, each returning a bare
# number as plain text rather than JSON.
BUY_URL = "https://dichikash.com/ajax/dolar-compra.php"
SELL_URL = "https://dichikash.com/ajax/dolar-venta.php"


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    try:
        buy_price = float(str(data["buy"]).strip())
        sell_price = float(str(data["sell"]).strip())
    except (KeyError, ValueError, TypeError):
        msg = "No valid exchange rates parsed"
        raise ValueError(msg) from None

    if buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [
        ExchangeRate(
            name="dichikash",
            buy_price=buy_price,
            sell_price=sell_price,
            timestamp=datetime.now(timezone.utc),
        )
    ]


async def fetch_dichikash(
    client: httpx.AsyncClient,
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch(c: httpx.AsyncClient) -> list[ExchangeRate]:
        buy_response = await c.get(BUY_URL, timeout=timeout)
        buy_response.raise_for_status()
        sell_response = await c.get(SELL_URL, timeout=timeout)
        sell_response.raise_for_status()
        return _parse_json({"buy": buy_response.text, "sell": sell_response.text})

    return await fetch_with_retry(client, _fetch, max_retries, retry_delay, BUY_URL)
