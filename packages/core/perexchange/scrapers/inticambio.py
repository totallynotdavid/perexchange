import html
import json
import re

from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import html_scraper, rate_from_fields


URL = "https://inticambio.pe/"

# The page is server-rendered by Inertia.js: the initial props (including the
# current rate) are embedded as an HTML-escaped JSON blob in a `data-page`
# attribute rather than fetched separately by the client.
_DATA_PAGE = re.compile(r'data-page="([^"]*)"')


def _parse_html(html_content: str) -> list[ExchangeRate]:
    latest = _latest_rate(html_content)
    if not latest:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    timestamp = datetime.now(timezone.utc)
    rate = rate_from_fields(latest, "inticambio", "tc_Compra", "tc_Venta", timestamp)
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


fetch_inticambio = html_scraper(URL, _parse_html)
