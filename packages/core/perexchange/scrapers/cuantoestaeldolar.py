import json
import re

from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import html_scraper


URL = "https://cuantoestaeldolar.pe/cambio-de-dolar-online"

# A plain GET returns exchange-house data in a Next.js flight payload, not in rendered
# markup. Read the `self.__next_f.push(...)` rows because the DOM is populated after
# client hydration.
_PUSH_CALL = re.compile(r"self\.__next_f\.push\(")
_HOUSE_LIST_MARKER = '"type":"ONLINE-HOUSE"'


def _extract_balanced(text: str, start: int) -> str | None:
    """Extract a bracket-balanced `[...]` substring starting at `start`, string-aware."""
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _flight_rows(html_content: str) -> list[str]:
    """Decode each `self.__next_f.push([...])` call's row string from the page."""
    rows = []
    for match in _PUSH_CALL.finditer(html_content):
        array_start = html_content.index("[", match.end() - 1)
        raw_array = _extract_balanced(html_content, array_start)
        if raw_array is None:
            continue
        try:
            segment = json.loads(raw_array)
        except ValueError:
            continue
        if len(segment) > 1 and isinstance(segment[1], str):
            rows.append(segment[1])
    return rows


def _find_houses(html_content: str) -> list[dict[str, Any]] | None:
    # A page can embed preview and full-list rows. The complete listing is the longest
    # candidate in the response.
    best: list[dict[str, Any]] | None = None
    for row in _flight_rows(html_content):
        if _HOUSE_LIST_MARKER not in row:
            continue
        array_start = row.find('[{"id"')
        if array_start == -1:
            continue
        raw_array = _extract_balanced(row, array_start)
        if raw_array is None:
            continue
        try:
            houses = json.loads(raw_array)
        except ValueError:
            continue
        if (
            isinstance(houses, list)
            and houses
            and (best is None or len(houses) > len(best))
        ):
            best = houses
    return best


def _parse_timestamp(raw: Any) -> datetime:
    if raw:
        try:
            return datetime.fromtimestamp(int(raw) / 1000, tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass
    return datetime.now(timezone.utc)


def _house_to_rate(house: dict[str, Any]) -> ExchangeRate | None:
    # Status 1 means the house is currently shown. Hidden listings can keep stale or
    # blank rate fields.
    if house.get("status") != 1:
        return None

    name = house.get("title")
    if not isinstance(name, str) or not name.strip():
        return None

    try:
        rates = house["rates"]
        buy_price = float(rates["buy"]["cost"])
        sell_price = float(rates["sale"]["cost"])
    except (KeyError, ValueError, TypeError):
        return None

    if buy_price <= 0 or sell_price <= 0:
        return None

    return ExchangeRate(
        name=name.strip(),
        buy_price=buy_price,
        sell_price=sell_price,
        timestamp=_parse_timestamp(house.get("timestamp")),
    )


def _parse_html(html_content: str) -> list[ExchangeRate]:
    houses = _find_houses(html_content)
    if not houses:
        msg = "No exchange houses found in HTML"
        raise ValueError(msg)

    rates = [rate for house in houses if (rate := _house_to_rate(house)) is not None]

    if not rates:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)

    # The aggregator must not return a quote covered by a dedicated adapter.
    from perexchange.scrapers.registry import is_registered_house

    return [rate for rate in rates if not is_registered_house(rate.name)]


fetch_cuantoestaeldolar = html_scraper(URL, _parse_html)
