from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.retry import fetch_with_retry


SOURCE = "okane"
BASE_URL = "https://okanecambiodigital.com/backend_apigateway/v1/tipoDeCambio"

# The API expects the current date in Peru. At UTC midnight, it may still have no data
# for the new date, so use the source's timezone when building the request.
_PERU_TZ = timezone(timedelta(hours=-5))


def _parse_json(response_data: list[dict[str, Any]]) -> list[ExchangeRate]:
    for entry in response_data:
        if entry.get("idMoneda") != "USD":
            continue
        try:
            buy_price = float(entry["valorCompra"])
            sell_price = float(entry["valorVenta"])
        except (KeyError, ValueError, TypeError):
            continue
        if buy_price <= 0 or sell_price <= 0:
            continue
        return [
            ExchangeRate(
                source=SOURCE,
                name=SOURCE,
                buy_price=buy_price,
                sell_price=sell_price,
                timestamp=datetime.now(timezone.utc),
            )
        ]

    msg = "No valid exchange rates parsed"
    raise ValueError(msg)


async def fetch_okane(
    client: httpx.AsyncClient,
    timeout: float = 10.0,
    max_attempts: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch(c: httpx.AsyncClient) -> list[ExchangeRate]:
        today = datetime.now(_PERU_TZ).date()
        response = await c.get(
            BASE_URL, params={"fecha": today.isoformat()}, timeout=timeout
        )
        response.raise_for_status()
        return _parse_json(response.json())

    return await fetch_with_retry(client, _fetch, max_attempts, retry_delay, BASE_URL)
