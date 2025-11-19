from datetime import datetime, timezone

import httpx

from bs4 import BeautifulSoup
from bs4.element import Tag

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://app.dollarhouse.pe/calculadorav2"


async def fetch_dollarhouse(
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch(client: httpx.AsyncClient) -> list[ExchangeRate]:
        response = await client.get(URL)
        response.raise_for_status()
        return _parse_html(response.text)

    return await fetch_with_retry(_fetch, timeout, max_retries, retry_delay, URL)


def _parse_html(html_content: str) -> list[ExchangeRate]:
    soup = BeautifulSoup(html_content, "html.parser")

    buy_price = None
    sell_price = None

    # Prioritize visual display elements
    compra_div = soup.find("div", class_="exchange-rate purchase")
    venta_div = soup.find("div", class_="exchange-rate sale")

    if compra_div and venta_div:
        buy_price = _extract_rate_from_div(compra_div)
        sell_price = _extract_rate_from_div(venta_div)

    # Fallback to hidden inputs if visual not found
    if buy_price is None or sell_price is None:
        purchase_input = soup.find("input", id="purchaseprice")
        sale_input = soup.find("input", id="op_saleprice")

        if purchase_input:
            value = purchase_input.get("value")
            buy_price = _parse_float(value if isinstance(value, str) else None)
        if sale_input:
            value = sale_input.get("value")
            sell_price = _parse_float(value if isinstance(value, str) else None)

    if buy_price is None or sell_price is None or buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    timestamp = datetime.now(timezone.utc)
    return [
        ExchangeRate(
            name="dollarhouse",
            buy_price=buy_price,
            sell_price=sell_price,
            timestamp=timestamp,
        )
    ]


def _extract_rate_from_div(rate_div: Tag) -> float | None:
    span = rate_div.find("span")
    if span:
        text = span.get_text(strip=True)
        # Extract number after S/
        if text.startswith("S/"):
            return _parse_float(text[3:])
    return None


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
