from datetime import datetime, timezone
from typing import Any

import httpx

from bs4 import BeautifulSoup

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


PAGE_URL = "https://www.westernunionperu.pe/cambiodemoneda"
API_URL = "https://www.westernunionperu.pe/cambiodemoneda/Operation/PostTipoCambio"


async def fetch_westernunion(
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch(client: httpx.AsyncClient) -> list[ExchangeRate]:
        page_response = await client.get(PAGE_URL)
        page_response.raise_for_status()

        token = _extract_verification_token(page_response.text)

        api_response = await client.post(
            API_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": PAGE_URL,
            },
            data={
                "monto": "1000",
                "moneda": "2",
                "tipo": "1",
                "__RequestVerificationToken": token,
                "ERequestServicesGeneral[Recaptcha]": "",
            },
        )
        api_response.raise_for_status()

        return _parse_json(api_response.json())

    return await fetch_with_retry(_fetch, timeout, max_retries, retry_delay, API_URL)


def _extract_verification_token(html_content: str) -> str:
    """Extract CSRF token from Western Union page."""
    soup = BeautifulSoup(html_content, "html.parser")
    token_input = soup.find("input", {"name": "__RequestVerificationToken"})

    if not token_input:
        msg = "Could not find verification token on page"
        raise ValueError(msg)

    token = token_input.get("value")
    if not token or not isinstance(token, str):
        msg = "Verification token is empty or invalid"
        raise ValueError(msg)

    return token


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
