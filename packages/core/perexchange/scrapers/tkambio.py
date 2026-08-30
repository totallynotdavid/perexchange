from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://tkambio.com/wp-admin/admin-ajax.php"


async def fetch_tkambio(
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch(client: httpx.AsyncClient) -> list[ExchangeRate]:
        response = await client.post(
            URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            },
            data={"action": "get_exchange_rate"},
        )
        response.raise_for_status()
        return _parse_json(response.json())

    return await fetch_with_retry(_fetch, timeout, max_retries, retry_delay, URL)


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)
    rates = []

    base_rate = _try_create_rate(
        data, "tkambio", "buying_rate", "selling_rate", timestamp
    )
    if base_rate:
        rates.append(base_rate)

    for discount in data.get("discounts", []):
        try:
            min_amount = discount["min_amount"]
            buy_price = float(discount["buying_rate"])
            sell_price = float(discount["selling_rate"])
            if buy_price > 0 and sell_price > 0:
                rates.append(
                    ExchangeRate(
                        name=f"tkambio_{min_amount}",
                        buy_price=buy_price,
                        sell_price=sell_price,
                        timestamp=timestamp,
                    )
                )
        except (KeyError, ValueError, TypeError):
            continue

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
