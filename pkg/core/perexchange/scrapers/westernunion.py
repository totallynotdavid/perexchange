import asyncio

from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate


PAGE_URL = "https://www.westernunionperu.pe/cambiodemoneda"
API_URL = "https://www.westernunionperu.pe/cambiodemoneda/Operation/PostTipoCambio"


async def fetch_westernunion(
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    last_error = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # First get the page to establish session and get verification token
                page_response = await client.get(PAGE_URL)
                page_response.raise_for_status()

                # Extract verification token
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(page_response.text, "html.parser")
                token_input = soup.find("input", {"name": "__RequestVerificationToken"})
                if not token_input:
                    msg = "Could not find verification token on page"
                    raise ValueError(msg)

                token = token_input.get("value")
                if not token:
                    msg = "Verification token is empty"
                    raise ValueError(msg)

                # Now call the API
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": PAGE_URL,
                }

                data = {
                    "monto": "1000",
                    "moneda": "2",
                    "tipo": "1",
                    "__RequestVerificationToken": token,
                    "ERequestServicesGeneral[Recaptcha]": "",
                }

                api_response = await client.post(API_URL, headers=headers, data=data)
                api_response.raise_for_status()

                return _parse_json(api_response.json())

        except httpx.HTTPError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)
                await asyncio.sleep(wait_time)
            continue

        except (ValueError, KeyError, TypeError) as e:
            msg = (
                f"Failed to parse exchange rates from {API_URL}. "
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
        buy_price = float(data["DT_Compra"])
        sell_price = float(data["DT_Venta"])
        if buy_price > 0 and sell_price > 0:
            rates.append(
                ExchangeRate(
                    name="westernunion",
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
