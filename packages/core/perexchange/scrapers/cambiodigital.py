from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import json_scraper, rate_from_fields


SOURCE = "cambiodigital"
URL = "https://cambiodigital.pseperu.pro/api/exchange-rates/last-exchange-rate"


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)

    rate = rate_from_fields(
        data, SOURCE, SOURCE, "priceCompra", "priceVenta", timestamp
    )
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


fetch_cambiodigital = json_scraper(SOURCE, URL, _parse_json)
