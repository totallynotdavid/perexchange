from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import json_scraper


URL = "https://www.mercadocambiario.pe/api/mercado/get/admin-data"


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    # The order book has no stable quote. Use adminOpenData, the published reference
    # also shown by cuantoestaeldolar. `typeExchangeStart` is the sale price, while
    # `typeExchangeDetraction` is the seller's net amount and maps to `buy_price`.
    try:
        open_data = data["adminOpenData"]
        buy_price = float(open_data["typeExchangeDetraction"])
        sell_price = float(open_data["typeExchangeStart"])
    except (KeyError, ValueError, TypeError):
        msg = "No valid exchange rates parsed"
        raise ValueError(msg) from None

    if buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [
        ExchangeRate(
            name="mercadocambiario",
            buy_price=buy_price,
            sell_price=sell_price,
            timestamp=datetime.now(timezone.utc),
        )
    ]


fetch_mercadocambiario = json_scraper(URL, _parse_json, method="POST", data={})
