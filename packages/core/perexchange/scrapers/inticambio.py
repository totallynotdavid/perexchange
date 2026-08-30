import html
import json
import re

from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import html_scraper, rate_from_fields


SOURCE = "inticambio"
URL = "https://inticambio.pe/"

# The page embeds its initial Inertia.js props, including the current rate, as an
# HTML-escaped JSON blob in `data-page`. There is no separate rate request to call.
_DATA_PAGE = re.compile(r'data-page="([^"]*)"')


def _parse_html(html_content: str) -> list[ExchangeRate]:
    latest = _latest_rate(html_content)
    if not latest:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    timestamp = datetime.now(timezone.utc)
    rate = rate_from_fields(latest, SOURCE, SOURCE, "tc_Compra", "tc_Venta", timestamp)
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


def _latest_rate(html_content: str) -> Any:
    match = _DATA_PAGE.search(html_content)
    if match is None:
        return None
    try:
        page = json.loads(html.unescape(match.group(1)))
        return page["props"]["latestExchangeRate"]
    except (ValueError, KeyError, TypeError):
        return None


fetch_inticambio = html_scraper(SOURCE, URL, _parse_html)
