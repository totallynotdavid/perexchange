from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import json_scraper, rate_from_fields


URL = "https://api.cambioseguro.com/api/v1.1/config/rates"

_RATE_CONFIGS = [
    ("cambioseguro", "purchase_price", "sale_price"),
    (
        "cambioseguro_comparative",
        "purchase_price_comparative",
        "sale_price_comparative",
    ),
    ("cambioseguro_paralelo", "purchase_price_paralelo", "sale_price_paralelo"),
]


def _parse_json(response_data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)
    data = response_data.get("data", {})

    rates = [
        rate
        for name, buy_key, sell_key in _RATE_CONFIGS
        if (rate := rate_from_fields(data, name, buy_key, sell_key, timestamp))
    ]

    if not rates:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return rates


fetch_cambioseguro = json_scraper(URL, _parse_json)
