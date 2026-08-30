from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import json_scraper, rate_from_fields


URL = "https://tkambio.com/wp-admin/admin-ajax.php"


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    timestamp = datetime.now(timezone.utc)
    rates = []

    base_rate = rate_from_fields(
        data, "tkambio", "buying_rate", "selling_rate", timestamp
    )
    if base_rate:
        rates.append(base_rate)

    for discount in data.get("discounts", []):
        min_amount = discount.get("min_amount")
        if min_amount is None:
            continue
        rate = rate_from_fields(
            discount, f"tkambio_{min_amount}", "buying_rate", "selling_rate", timestamp
        )
        if rate:
            rates.append(rate)

    if not rates:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return rates


fetch_tkambio = json_scraper(
    URL,
    _parse_json,
    method="POST",
    headers={
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    },
    data={"action": "get_exchange_rate"},
)
