from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://apim.tucambista.pe/api/rates"


async def fetch_tucambista(
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch(client: httpx.AsyncClient) -> list[ExchangeRate]:
        response = await client.get(
            URL,
            headers={
                "ocp-apim-subscription-key": "e4b6947d96a940e7bb8b39f462bcc56d;product=tucambista-production",
            },
        )
        response.raise_for_status()
        return _parse_json(response.json())

    return await fetch_with_retry(_fetch, timeout, max_retries, retry_delay, URL)


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)
    rates = []

    try:
        buy_price = float(data["bidRate"])
        sell_price = float(data["offerRate"])
        if buy_price > 0 and sell_price > 0:
            rates.append(
                ExchangeRate(
                    name="tucambista",
                    buy_price=buy_price,
                    sell_price=sell_price,
                    timestamp=timestamp,
                )
            )
    except (KeyError, ValueError, TypeError):
        pass

    if not rates:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return rates
