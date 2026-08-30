from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import json_scraper, rate_from_fields


SOURCE = "tucambista"
URL = "https://apim.tucambista.pe/api/rates"


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)

    rate = rate_from_fields(data, SOURCE, SOURCE, "bidRate", "offerRate", timestamp)
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


fetch_tucambista = json_scraper(
    SOURCE,
    URL,
    _parse_json,
    headers={
        "ocp-apim-subscription-key": "e4b6947d96a940e7bb8b39f462bcc56d;product=tucambista-production",
    },
)
