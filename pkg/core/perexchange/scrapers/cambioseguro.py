import asyncio

from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate


DEFAULT_URL = "https://api.cambioseguro.com/api/v1.1/config/rates"


async def fetch_cambioseguro(
    url: str = DEFAULT_URL,
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    last_error = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return _parse_json(response.json())

        except httpx.HTTPError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)
                await asyncio.sleep(wait_time)
            continue

        except (ValueError, KeyError, TypeError) as e:
            msg = (
                f"Failed to parse exchange rates from {url}. "
                "The API structure may have changed."
            )
            raise ValueError(msg) from e

    if last_error is None:
        msg = "Failed to fetch rates: no attempts were made"
        raise ValueError(msg)
    raise last_error


def _parse_json(response_data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)
    rates = []

    data = response_data.get("data", {})

    # Main rate
    try:
        buy_price = float(data["purchase_price"])
        sell_price = float(data["sale_price"])
        if buy_price > 0 and sell_price > 0:
            rates.append(
                ExchangeRate(
                    name="cambioseguro",
                    buy_price=buy_price,
                    sell_price=sell_price,
                    timestamp=timestamp,
                )
            )
    except (KeyError, ValueError, TypeError):
        pass

    # Comparative rate
    try:
        buy_price = float(data["purchase_price_comparative"])
        sell_price = float(data["sale_price_comparative"])
        if buy_price > 0 and sell_price > 0:
            rates.append(
                ExchangeRate(
                    name="cambioseguro_comparative",
                    buy_price=buy_price,
                    sell_price=sell_price,
                    timestamp=timestamp,
                )
            )
    except (KeyError, ValueError, TypeError):
        pass

    # Paralelo rate
    try:
        buy_price = float(data["purchase_price_paralelo"])
        sell_price = float(data["sale_price_paralelo"])
        if buy_price > 0 and sell_price > 0:
            rates.append(
                ExchangeRate(
                    name="cambioseguro_paralelo",
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
