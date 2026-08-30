from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import json_scraper


SOURCE = "metafx"
URL = "https://metafxperu.com/obtener_tasas.php"


def _parse_json(response_data: dict[str, Any]) -> list[ExchangeRate]:
    entries = response_data.get("data", [])
    buy_price = _rate_for(entries, "bid")
    sell_price = _rate_for(entries, "ask")

    if buy_price is None or sell_price is None or buy_price <= 0 or sell_price <= 0:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [
        ExchangeRate(
            source=SOURCE,
            name=SOURCE,
            buy_price=buy_price,
            sell_price=sell_price,
            timestamp=datetime.now(timezone.utc),
        )
    ]


def _rate_for(entries: list[dict[str, Any]], tipo: str) -> float | None:
    for entry in entries:
        if entry.get("tipo") != tipo:
            continue
        try:
            return float(entry["valor_fijo"])
        except (KeyError, ValueError, TypeError):
            return None
    return None


fetch_metafx = json_scraper(SOURCE, URL, _parse_json)
