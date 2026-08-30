from datetime import datetime, timezone

from bs4 import BeautifulSoup
from bs4.element import Tag

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import html_scraper


SOURCE = "moneyhouse"
URL = "https://moneyhouse.pe/"


def _parse_html(html_content: str) -> list[ExchangeRate]:
    soup = BeautifulSoup(html_content, "html.parser")

    buy_price = _extract_rate(soup, "views-field-field-t-c-compra")
    sell_price = _extract_rate(soup, "views-field-field-t-c-venta")

    if buy_price is None or sell_price is None or buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    timestamp = datetime.now(timezone.utc)
    return [
        ExchangeRate(
            source=SOURCE,
            name=SOURCE,
            buy_price=buy_price,
            sell_price=sell_price,
            timestamp=timestamp,
        )
    ]


def _extract_rate(soup: BeautifulSoup, field_class: str) -> float | None:
    field = soup.find("div", class_=field_class)
    if not isinstance(field, Tag):
        return None
    span = field.find("span", class_="cantant")
    if not isinstance(span, Tag):
        return None
    try:
        return float(span.get_text(strip=True))
    except ValueError:
        return None


fetch_moneyhouse = html_scraper(SOURCE, URL, _parse_html)
