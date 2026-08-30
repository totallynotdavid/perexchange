import re

from datetime import datetime, timezone

from bs4 import BeautifulSoup

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import html_scraper


SOURCE = "cambiosol"
URL = "https://cambiosol.pe/"

_RATE = re.compile(r"S/\s*([\d.]+)")


def _extract_rate(soup: BeautifulSoup, element_id: str) -> float | None:
    element = soup.find(id=element_id)
    if element is None:
        return None
    match = _RATE.search(element.get_text())
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _parse_html(html_content: str) -> list[ExchangeRate]:
    soup = BeautifulSoup(html_content, "html.parser")

    buy_price = _extract_rate(soup, "buy-rate-display")
    sell_price = _extract_rate(soup, "sell-rate-display")

    if buy_price is None or sell_price is None or buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [
        ExchangeRate(
            source=SOURCE,
            name="cambiosol",
            buy_price=buy_price,
            sell_price=sell_price,
            timestamp=datetime.now(timezone.utc),
        )
    ]


fetch_cambiosol = html_scraper(SOURCE, URL, _parse_html)
