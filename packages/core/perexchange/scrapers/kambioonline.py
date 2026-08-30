from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import json_scraper, rate_from_fields


URL = "https://kambio.com.pe/api/rates/current"


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)

    rate = rate_from_fields(data, "kambioonline", "buy", "sell", timestamp)
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


fetch_kambioonline = json_scraper(URL, _parse_json)
