import asyncio

from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate


DEFAULT_URL = "https://apim.tucambista.pe/api/rates"


async def fetch_tucambista(
    url: str = DEFAULT_URL,
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    last_error = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                headers = {
                    "accept": "application/json, text/plain, */*",
                    "channel": "web",
                    "ocp-apim-subscription-key": "e4b6947d96a940e7bb8b39f462bcc56d;product=tucambista-production",
                }
                response = await client.get(url, headers=headers)
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
