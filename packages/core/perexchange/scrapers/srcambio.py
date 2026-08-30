from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import json_scraper
from perexchange.time import parse_source_timestamp


SOURCE = "srcambio"
URL = "https://srcambio.pseperu.pro/api/exchange-rates/last-exchange-rate"


def _parse_json(response_data: dict[str, Any]) -> list[ExchangeRate]:
    try:
        buy_price = float(response_data["priceCompra"])
        sell_price = float(response_data["priceVenta"])
    except (KeyError, ValueError, TypeError) as e:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg) from e

    if buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    timestamp = parse_source_timestamp(
        response_data.get("dateRegister"), datetime.now(timezone.utc)
    )

    return [
        ExchangeRate(
            source=SOURCE,
            name=SOURCE,
            buy_price=buy_price,
            sell_price=sell_price,
            timestamp=timestamp,
        )
    ]


fetch_srcambio = json_scraper(SOURCE, URL, _parse_json)
