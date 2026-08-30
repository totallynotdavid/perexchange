from datetime import datetime, timezone

import httpx

from bs4 import BeautifulSoup
from bs4.element import Tag

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import fetch_with_retry


URL = "https://cuantoestaeldolar.pe/cambio-de-dolar-online"


async def fetch_cuantoestaeldolar(
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
    soup = BeautifulSoup(html_content, "lxml")
    change_buttons = soup.find_all("a", string="CAMBIAR")  # type: ignore[call-overload]

    if not change_buttons:
        msg = "No exchange houses found in HTML"
        raise ValueError(msg)

    timestamp = datetime.now(timezone.utc)
    rates = []

    for button in change_buttons:
        try:
            rate = _extract_rate_from_card(button, timestamp)
            if rate:
                rates.append(rate)
        except (AttributeError, ValueError, TypeError, IndexError):
            continue

    if not rates:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return rates


def _extract_rate_from_card(button: Tag, timestamp: datetime) -> ExchangeRate | None:
    parent = button.find_parent("div")
    if not parent:
        return None
    card = parent.find_parent("div")
    if not card:
        return None

    img_tag = card.find("img")
    if not img_tag:
        return None
    alt_attr = img_tag.get("alt")
    name = alt_attr.strip() if isinstance(alt_attr, str) else None
    if not name:
        return None

    buy_block = card.select_one('div[class*="_content_buy__"]')
    sell_block = card.select_one('div[class*="_content_sale__"]')

    if not buy_block or not sell_block:
        return None

    buy_rate_elem = buy_block.find(
        "p", class_=lambda c: c and c.startswith("ValueCurrency_item_cost__")
    )
    buy_price = float(buy_rate_elem.text) if buy_rate_elem else None

    sell_rate_elem = sell_block.find(
        "p", class_=lambda c: c and c.startswith("ValueCurrency_item_cost__")
    )
    sell_price = float(sell_rate_elem.text) if sell_rate_elem else None

    if not buy_price or not sell_price or buy_price <= 0 or sell_price <= 0:
        return None

    return ExchangeRate(
        name=name,
        buy_price=buy_price,
        sell_price=sell_price,
        timestamp=timestamp,
    )
