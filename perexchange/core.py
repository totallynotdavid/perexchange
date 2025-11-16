import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import mean
from typing import List, Literal, Optional

import httpx
from bs4 import BeautifulSoup

DEFAULT_URL = "https://cuantoestaeldolar.pe/cambio-de-dolar-online"


@dataclass
class ExchangeRate:
    """
    Exchange rate data for a single exchange house.

    Attributes:
        name: Exchange house name
        buy_price: Price to buy USD (in PEN)
        sell_price: Price to sell USD (in PEN)
        timestamp: When this rate was fetched
    """

    name: str
    buy_price: float
    sell_price: float
    timestamp: datetime

    @property
    def spread(self) -> float:
        """Calculate the spread (sell - buy)."""
        return self.sell_price - self.buy_price

    def __repr__(self) -> str:
        return (
            f"ExchangeRate(name={self.name!r}, "
            f"buy={self.buy_price:.4f}, sell={self.sell_price:.4f})"
        )


async def fetch_rates(
    url: str = DEFAULT_URL,
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> List[ExchangeRate]:
    """
    Fetch current exchange rates by scraping the website.

    Args:
        url: Website URL to scrape
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                html_content = response.text

                soup = BeautifulSoup(html_content, "lxml")

                # Find all "CAMBIAR" buttons as stable anchors
                change_buttons = soup.find_all("a", string="CAMBIAR")

                if not change_buttons:
                    raise ValueError("No exchange houses found in HTML")

                timestamp = datetime.now(UTC)
                rates = []

                for button in change_buttons:
                    try:
                        # The card is the grandparent of the button element
                        card = button.find_parent("div").find_parent("div")
                        if not card:
                            continue

                        # Get name from img alt attribute
                        img_tag = card.find("img")
                        name = img_tag["alt"].strip() if img_tag else None

                        if not name:
                            continue

                        # Find buy and sell rate blocks
                        buy_block = card.select_one('div[class*="_content_buy__"]')
                        sell_block = card.select_one('div[class*="_content_sale__"]')

                        if not buy_block or not sell_block:
                            continue

                        # Get buy rate
                        buy_rate_elem = buy_block.find(
                            "p", class_=lambda c: c and c.startswith("ValueCurrency_item_cost__")
                        )
                        buy_price = float(buy_rate_elem.text) if buy_rate_elem else None

                        # Get sell rate
                        sell_rate_elem = sell_block.find(
                            "p", class_=lambda c: c and c.startswith("ValueCurrency_item_cost__")
                        )
                        sell_price = float(sell_rate_elem.text) if sell_rate_elem else None

                        # Validate prices
                        if not buy_price or not sell_price or buy_price <= 0 or sell_price <= 0:
                            continue

                        rates.append(
                            ExchangeRate(
                                name=name,
                                buy_price=buy_price,
                                sell_price=sell_price,
                                timestamp=timestamp,
                            )
                        )
                    except (AttributeError, ValueError, TypeError, IndexError):
                        continue

                if not rates:
                    raise ValueError("No valid exchange rates parsed")

                return rates

        except (httpx.HTTPError, ValueError) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)
                await asyncio.sleep(wait_time)
            continue

    raise last_error


def find_best_buy(rates: List[ExchangeRate]) -> Optional[ExchangeRate]:
    """
    Find the best place to buy USD (lowest buy price)
    """
    if not rates:
        return None
    return min(rates, key=lambda r: r.buy_price)


def find_best_sell(rates: List[ExchangeRate]) -> Optional[ExchangeRate]:
    """
    Find the best place to sell USD (highest sell price)
    """
    if not rates:
        return None
    return max(rates, key=lambda r: r.sell_price)


def get_top_n(
    rates: List[ExchangeRate], n: int = 3, operation: Literal["buy", "sell"] = "buy"
) -> List[ExchangeRate]:
    """
    Get top N exchange houses for buying or selling.

    Args:
        rates: List of exchange rates
        n: Number of top exchanges to return
        operation: 'buy' (lowest prices) or 'sell' (highest prices)
    """
    if not rates:
        return []

    if operation == "buy":
        # Sort by buy price ascending (lowest first)
        sorted_rates = sorted(rates, key=lambda r: r.buy_price)
    else:
        # Sort by sell price descending (highest first)
        sorted_rates = sorted(rates, key=lambda r: r.sell_price, reverse=True)

    return sorted_rates[:n]


def calculate_average(
    rates: List[ExchangeRate], operation: Literal["buy", "sell"] = "buy"
) -> Optional[float]:
    """
    Calculate average buy or sell price across all exchange houses.

    Args:
        rates: List of exchange rates
        operation: 'buy' or 'sell'
    """
    if not rates:
        return None

    if operation == "buy":
        prices = [r.buy_price for r in rates]
    else:
        prices = [r.sell_price for r in rates]

    return mean(prices)


def calculate_spread(rates: List[ExchangeRate]) -> Optional[float]:
    """
    Calculate the average spread across all exchange houses.
    The spread is the difference between sell and buy prices.
    """
    if not rates:
        return None

    spreads = [r.spread for r in rates]
    return mean(spreads)


def filter_by_price_range(
    rates: List[ExchangeRate],
    operation: Literal["buy", "sell"],
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[ExchangeRate]:
    """
    Filter exchange rates by price range.

    Args:
        rates: List of exchange rates
        operation: 'buy' or 'sell'
        min_price: Minimum price (inclusive)
        max_price: Maximum price (inclusive)
    """
    filtered = rates

    if operation == "buy":
        if min_price is not None:
            filtered = [r for r in filtered if r.buy_price >= min_price]
        if max_price is not None:
            filtered = [r for r in filtered if r.buy_price <= max_price]
    else:
        if min_price is not None:
            filtered = [r for r in filtered if r.sell_price >= min_price]
        if max_price is not None:
            filtered = [r for r in filtered if r.sell_price <= max_price]

    return filtered
