from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import json_scraper, rate_from_fields


SOURCE = "marketdollar"
URL = "https://market-dollar.com/api/exchange-rate"


def _parse_json(response_data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)
    rate = rate_from_fields(response_data, SOURCE, SOURCE, "compra", "venta", timestamp)
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


fetch_marketdollar = json_scraper(SOURCE, URL, _parse_json)
