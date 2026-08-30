from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import json_scraper


URL = "https://api.defiperu.com/api/ExchangeRates/currencyType?currencyType=FIAT"


def _parse_json(data: list[dict[str, Any]]) -> list[ExchangeRate]:
    entry = next(
        (
            d
            for d in data
            if d.get("fromCurrency") == "PEN" and d.get("toCurrency") == "USD"
        ),
        None,
    )
    if entry is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    try:
        buy_price = float(entry["purchase"])
        sell_price = float(entry["sale"])
    except (KeyError, ValueError, TypeError):
        msg = "No valid exchange rates parsed"
        raise ValueError(msg) from None

    if buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [
        ExchangeRate(
            name="defiperu",
            buy_price=buy_price,
            sell_price=sell_price,
            timestamp=datetime.now(timezone.utc),
        )
    ]


fetch_defiperu = json_scraper(URL, _parse_json)
