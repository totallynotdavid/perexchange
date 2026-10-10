from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import json_scraper, rate_from_fields
from perexchange.time import PERU_TZ, parse_source_timestamp


SOURCE = "cambiomundial"
URL = "https://www.cambiomundial.com/backend/tasaCambio/daily"


def _parse_json(response_data: list[dict[str, Any]]) -> list[ExchangeRate]:
    # The endpoint also returns a DIFERENCIADA tier for large amounts. REGULAR is the
    # rate shown publicly.
    entry = next(
        (item for item in response_data if item.get("tipoTasa") == "REGULAR"), None
    )
    # `fecha` has no offset and is local time in Peru.
    timestamp = parse_source_timestamp(
        entry.get("fecha") if entry else None, datetime.now(timezone.utc), PERU_TZ
    )
    rate = (
        rate_from_fields(entry, SOURCE, SOURCE, "buy", "sell", timestamp)
        if entry
        else None
    )
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


fetch_cambiomundial = json_scraper(SOURCE, URL, _parse_json)
