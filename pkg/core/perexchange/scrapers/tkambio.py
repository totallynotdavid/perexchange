import asyncio

from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate


DEFAULT_URL = "https://tkambio.com/wp-admin/admin-ajax.php"


async def fetch_tkambio(
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
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                }
                data = {"action": "get_exchange_rate"}
                response = await client.post(url, headers=headers, data=data)
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

    # Base rate
    try:
        buy_price = float(data["buying_rate"])
        sell_price = float(data["selling_rate"])
        if buy_price > 0 and sell_price > 0:
            rates.append(
                ExchangeRate(
                    name="tkambio",
                    buy_price=buy_price,
                    sell_price=sell_price,
                    timestamp=timestamp,
                )
            )
    except (KeyError, ValueError, TypeError):
        pass

    # Discount rates
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
