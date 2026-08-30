from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.factories import json_scraper, rate_from_fields


SOURCE = "cambiafx"
URL = "https://apiluna.cambiafx.pe/api/BackendPizarra/getTcCustomerNoAuth?idParCurrency=1&codePromo=CED"


def _parse_json(response_data: list[dict[str, Any]]) -> list[ExchangeRate]:
    if not response_data:
        msg = "No exchange rates data"
        raise ValueError(msg)

    timestamp = datetime.now(timezone.utc)

    rate = rate_from_fields(
        response_data[0], SOURCE, SOURCE, "tcBuy", "tcSale", timestamp
    )
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    return [rate]


fetch_cambiafx = json_scraper(SOURCE, URL, _parse_json)
