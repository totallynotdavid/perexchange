from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import csrf_convert_scraper, rate_from_convert_fields


URL = "https://chaskidolar.com/"


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)

    rate = rate_from_convert_fields(data, "chaskidolar", timestamp)
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


fetch_chaskidolar = csrf_convert_scraper(URL, _parse_json)
