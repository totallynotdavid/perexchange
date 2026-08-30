from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import dual_endpoint_json_scraper


BUY_URL = "https://api.dolarex.pe/cotizacion/buscar/USDPEN"
SELL_URL = "https://api.dolarex.pe/cotizacion/buscar/PENUSD"


def _extract_rate(data: dict[str, Any]) -> float | None:
    try:
        return float(data["cotizacion"][0]["cotizacion"])
    except (KeyError, IndexError, ValueError, TypeError):
        return None


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    buy_price = _extract_rate(data.get("buy", {}))
    sell_price = _extract_rate(data.get("sell", {}))

    if buy_price is None or sell_price is None or buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [
        ExchangeRate(
            name="dolarex",
            buy_price=buy_price,
            sell_price=sell_price,
            timestamp=datetime.now(timezone.utc),
        )
    ]


fetch_dolarex = dual_endpoint_json_scraper(BUY_URL, SELL_URL, _parse_json)
