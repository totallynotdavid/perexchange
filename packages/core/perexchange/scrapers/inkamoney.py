from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import (
    csrf_convert_scraper,
    rate_from_convert_fields,
)


SOURCE = "inkamoney"
URL = "https://inkamoney.com/"


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)

    rate = rate_from_convert_fields(data, SOURCE, SOURCE, timestamp)
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


fetch_inkamoney = csrf_convert_scraper(SOURCE, URL, _parse_json)
