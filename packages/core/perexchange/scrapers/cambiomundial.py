from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import json_scraper, rate_from_fields


URL = "https://www.cambiomundial.com/backend/tasaCambio/daily"


def _parse_json(response_data: list[dict[str, Any]]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)

    # The endpoint also returns a DIFERENCIADA tier for large amounts; REGULAR
    # is the rate the site displays publicly.
    entry = next(
        (item for item in response_data if item.get("tipoTasa") == "REGULAR"), None
    )
    rate = (
        rate_from_fields(entry, "cambiomundial", "buy", "sell", timestamp)
        if entry
        else None
    )
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


fetch_cambiomundial = json_scraper(URL, _parse_json)
