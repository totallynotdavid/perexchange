import re

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any

import httpx

from perexchange.models import ExchangeRate
from perexchange.retry import fetch_with_retry
from perexchange.scrapers.base import ExchangeRateScraper


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
            response = await c.request(
                method, url, headers=headers, data=data, timeout=timeout
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
            response = await c.request(
                method, url, headers=headers, data=data, timeout=timeout
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
            buy_response = await c.get(buy_url, timeout=timeout)
            buy_response.raise_for_status()
            sell_response = await c.get(sell_url, timeout=timeout)
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
            page_response = await c.get(page_url, timeout=timeout)
            page_response.raise_for_status()
            token = _extract_csrf_token(page_response.text)
            api_response = await c.post(
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


def rate_from_convert_fields(
    data: Mapping[str, Any], source: str, name: str, timestamp: datetime
) -> ExchangeRate | None:
    return rate_from_fields(data, source, name, "fxBaseSale", "fxBaseBuy", timestamp)
