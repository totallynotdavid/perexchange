import re

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.retry import fetch_with_retry
from perexchange.scrapers.base import ExchangeRateScraper
from perexchange.time import PERU_TZ, parse_source_timestamp
from perexchange.transport import send


def _validate_rates(source: str, rates: list[ExchangeRate]) -> list[ExchangeRate]:
    if any(rate.source != source for rate in rates):
        msg = f"parser for {source} returned a rate with the wrong source ID"
        raise ValueError(msg)
    return rates


def rate_from_fields(
    data: Mapping[str, Any],
    source: str,
    name: str,
    buy_key: str,
    sell_key: str,
    timestamp: datetime,
) -> ExchangeRate | None:
    """Build a rate when both prices are positive finite numbers."""
    try:
        buy_price = float(data[buy_key])
        sell_price = float(data[sell_key])
    except (KeyError, ValueError, TypeError):
        return None
    if buy_price <= 0 or sell_price <= 0:
        return None
    return ExchangeRate(
        source=source,
        name=name,
        buy_price=buy_price,
        sell_price=sell_price,
        timestamp=timestamp,
    )


def json_scraper(
    source: str,
    url: str,
    parse: Callable[[Any], list[ExchangeRate]],
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
    data: Mapping[str, str] | None = None,
) -> ExchangeRateScraper:
    async def fetch(
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_attempts: int = 3,
        retry_delay: float = 0.5,
    ) -> list[ExchangeRate]:
        async def _fetch(c: httpx.AsyncClient) -> list[ExchangeRate]:
            response = await send(
                c, method, url, headers=headers, data=data, timeout=timeout
            )
            response.raise_for_status()
            return _validate_rates(source, parse(response.json()))

        return await fetch_with_retry(client, _fetch, max_attempts, retry_delay, url)

    return fetch


def html_scraper(
    source: str,
    url: str,
    parse: Callable[[str], list[ExchangeRate]],
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
    data: Mapping[str, str] | None = None,
) -> ExchangeRateScraper:
    async def fetch(
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_attempts: int = 3,
        retry_delay: float = 0.5,
    ) -> list[ExchangeRate]:
        async def _fetch(c: httpx.AsyncClient) -> list[ExchangeRate]:
            response = await send(
                c, method, url, headers=headers, data=data, timeout=timeout
            )
            response.raise_for_status()
            return _validate_rates(source, parse(response.text))

        return await fetch_with_retry(client, _fetch, max_attempts, retry_delay, url)

    return fetch


def dual_endpoint_json_scraper(
    source: str,
    buy_url: str,
    sell_url: str,
    parse: Callable[[dict[str, Any]], list[ExchangeRate]],
) -> ExchangeRateScraper:
    async def fetch(
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_attempts: int = 3,
        retry_delay: float = 0.5,
    ) -> list[ExchangeRate]:
        async def _fetch(c: httpx.AsyncClient) -> list[ExchangeRate]:
            buy_response = await send(c, "GET", buy_url, timeout=timeout)
            buy_response.raise_for_status()
            sell_response = await send(c, "GET", sell_url, timeout=timeout)
            sell_response.raise_for_status()
            rates = parse({"buy": buy_response.json(), "sell": sell_response.json()})
            return _validate_rates(source, rates)

        return await fetch_with_retry(
            client, _fetch, max_attempts, retry_delay, buy_url
        )

    return fetch


_CSRF_META = re.compile(r'name="csrf-token"\s+content="([^"]+)"')


def _extract_csrf_token(html_content: str) -> str:
    match = _CSRF_META.search(html_content)
    if not match:
        msg = "Could not find CSRF token on page"
        raise ValueError(msg)
    return match.group(1)


def csrf_convert_scraper(
    source: str,
    base_url: str,
    parse: Callable[[Any], list[ExchangeRate]],
) -> ExchangeRateScraper:
    page_url = base_url
    api_url = f"{base_url}convert"

    async def fetch(
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        max_attempts: int = 3,
        retry_delay: float = 0.5,
    ) -> list[ExchangeRate]:
        async def _fetch(c: httpx.AsyncClient) -> list[ExchangeRate]:
            page_response = await send(c, "GET", page_url, timeout=timeout)
            page_response.raise_for_status()
            token = _extract_csrf_token(page_response.text)
            api_response = await send(
                c,
                "POST",
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRF-TOKEN": token,
                    "Referer": page_url,
                },
                json={
                    "amount": 1000,
                    "currency": "PEN",
                    "type": "buy",
                    "credits": 0,
                },
                timeout=timeout,
            )
            api_response.raise_for_status()
            return _validate_rates(source, parse(api_response.json()))

        return await fetch_with_retry(
            client, _fetch, max_attempts, retry_delay, page_url
        )

    return fetch


DIGITAL_TC_URL = "https://novodivisaspro.pseperu.pro/api/digital/public/tc"


def digital_tc_parser(source: str) -> Callable[[Any], list[ExchangeRate]]:
    """Parse the response of the shared exchange-rate API behind `DIGITAL_TC_URL`."""

    def parse(data: Mapping[str, Any]) -> list[ExchangeRate]:
        if not data["disponible"]:
            msg = "The source reports no exchange rate available"
            raise ValueError(msg)
        # The server time has no offset and is local time in Peru.
        timestamp = parse_source_timestamp(
            data.get("serverTime"), datetime.now(timezone.utc), PERU_TZ
        )
        rate = rate_from_fields(data, source, source, "compra", "venta", timestamp)
        if rate is None:
            msg = "No valid exchange rates parsed"
            raise ValueError(msg)
        return [rate]

    return parse


def digital_tc_scraper(
    source: str, tenant: str, parse: Callable[[Any], list[ExchangeRate]]
) -> ExchangeRateScraper:
    """Fetch one house from the shared API. The tenant header selects the house."""
    return json_scraper(
        source, DIGITAL_TC_URL, parse, headers={"X-Digital-Tenant": tenant}
    )


def rate_from_convert_fields(
    data: Mapping[str, Any], source: str, name: str, timestamp: datetime
) -> ExchangeRate | None:
    return rate_from_fields(data, source, name, "fxBaseSale", "fxBaseBuy", timestamp)
