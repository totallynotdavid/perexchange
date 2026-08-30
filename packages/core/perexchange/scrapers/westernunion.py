from datetime import datetime, timezone
from typing import Any

import httpx

from bs4 import BeautifulSoup

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry, rate_from_fields


PAGE_URL = "https://www.westernunionperu.pe/cambiodemoneda"
API_URL = "https://www.westernunionperu.pe/cambiodemoneda/Operation/PostTipoCambio"


async def fetch_westernunion(
    client: httpx.AsyncClient,
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch_token(c: httpx.AsyncClient) -> str:
        page_response = await c.get(PAGE_URL, timeout=timeout)
        page_response.raise_for_status()
        return _extract_verification_token(page_response.text)

    token = await fetch_with_retry(
        client, _fetch_token, max_retries, retry_delay, PAGE_URL
    )

    async def _fetch_rate(c: httpx.AsyncClient) -> list[ExchangeRate]:
        api_response = await c.post(
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
            timeout=timeout,
        )
        api_response.raise_for_status()
        return _parse_json(api_response.json())

    return await fetch_with_retry(
        client, _fetch_rate, max_retries, retry_delay, API_URL
    )


def _extract_verification_token(html_content: str) -> str:
    """Read the ASP.NET verification token required by the quote request."""
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

    rate = rate_from_fields(data, "westernunion", "DT_Compra", "DT_Venta", timestamp)
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]
