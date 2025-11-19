import re

from datetime import datetime, timezone

import httpx

from bs4 import BeautifulSoup
from bs4.element import Tag

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://instakash.net/"


async def fetch_instakash(
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 0.5,
) -> list[ExchangeRate]:
    async def _fetch(client: httpx.AsyncClient) -> list[ExchangeRate]:
        response = await client.get(URL)
        response.raise_for_status()
        return _parse_html(response.text)

    return await fetch_with_retry(_fetch, timeout, max_retries, retry_delay, URL)


def _extract_rate_value(rate_div: Tag) -> float | None:
    rate_p = rate_div.find("p", class_="font-semibold")
    if not rate_p:
        return None

    text = rate_p.get_text(strip=True)
    match = re.search(r"\d+\.\d{4}", text)
    return float(match.group(0)) if match else None


def _parse_html(html_content: str) -> list[ExchangeRate]:
    soup = BeautifulSoup(html_content, "html.parser")

    rates_container = soup.find(
        "div", class_="flex items-center justify-center text-primary gap-10 py-1"
    )

    if not rates_container:
        msg = "Could not find the main rates container"
        raise ValueError(msg)

    rate_items = rates_container.find_all("div", recursive=False)

    if len(rate_items) < 3:
        msg = "Rates container structure is unexpected"
        raise ValueError(msg)

    compra_div = rate_items[0]
    venta_div = rate_items[2]

    buy_price = _extract_rate_value(compra_div)
    sell_price = _extract_rate_value(venta_div)

    if buy_price is None or sell_price is None or buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    timestamp = datetime.now(timezone.utc)
    rate = ExchangeRate(
        name="instakash",
        buy_price=buy_price,
        sell_price=sell_price,
        timestamp=timestamp,
    )

    return [rate]
