import asyncio

from datetime import datetime, timezone

import httpx

from bs4 import BeautifulSoup

from perexchange.models import ExchangeRate


DEFAULT_URL = "https://cuantoestaeldolar.pe/cambio-de-dolar-online"


async def fetch_cuantoestaeldolar(
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
                return _parse_html(response.text)

        except httpx.HTTPError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)
                await asyncio.sleep(wait_time)
            continue

        except (ValueError, AttributeError, TypeError, IndexError) as e:
            # Parsing errors indicate website structure changed (fail immediately)
            msg = (
                f"Failed to parse exchange rates from {url}. "
                "The website structure may have changed."
            )
            raise ValueError(msg) from e

    if last_error is None:
        msg = "Failed to fetch rates: no attempts were made"
        raise ValueError(msg)
    raise last_error


def _parse_html(html_content: str) -> list[ExchangeRate]:
    soup = BeautifulSoup(html_content, "lxml")
    change_buttons = soup.find_all("a", string="CAMBIAR")

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


def _extract_rate_from_card(button, timestamp: datetime) -> ExchangeRate | None:
    card = button.find_parent("div").find_parent("div")
    if not card:
        return None

    img_tag = card.find("img")
    name = img_tag["alt"].strip() if img_tag else None
    if not name:
        return None

    # Using partial class matching to handle CSS hash changes
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
