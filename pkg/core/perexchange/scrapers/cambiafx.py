from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://apiluna.cambiafx.pe/api/BackendPizarra/getTcCustomerNoAuth?idParCurrency=1&codePromo=CED"


async def fetch_cambiafx(
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
    if not response_data:
        msg = "No exchange rates data"
        raise ValueError(msg)

    timestamp = datetime.now(timezone.utc)
    rates = []

    # Take the first rate from the array
    data = response_data[0]
    try:
        buy_price = float(data["tcBuy"])
        sell_price = float(data["tcSale"])
        if buy_price > 0 and sell_price > 0:
            rate = ExchangeRate(
                name="cambiafx",
                buy_price=buy_price,
                sell_price=sell_price,
                timestamp=timestamp,
            )
            rates.append(rate)
    except (KeyError, ValueError, TypeError):
        pass

    if not rates:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return rates
