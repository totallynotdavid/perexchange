"""
Quick-start examples. Run: python examples.py (or uv run python examples.py)

"""

import asyncio
import json
import pathlib

from datetime import datetime, timezone
from statistics import mean

from perexchange import (
    fetch_rates,
    find_best_buy,
    find_best_sell,
)


def get_top_n(rates, n=3, operation="buy"):
    """Get top N rates by buy or sell price."""
    if operation == "buy":
        return sorted(rates, key=lambda r: r.buy_price)[:n]
    return sorted(rates, key=lambda r: r.sell_price, reverse=True)[:n]


def calculate_average(rates, operation="buy"):
    """Calculate average buy or sell price."""
    if operation == "buy":
        prices = [r.buy_price for r in rates]
    else:
        prices = [r.sell_price for r in rates]
    return mean(prices) if prices else None


def calculate_spread(rates):
    """Calculate average spread."""
    spreads = [r.spread for r in rates]
    return mean(spreads) if spreads else None


async def best_prices():
    """Show the best buy and sell prices right now."""
    rates = await fetch_rates()

    buy = find_best_buy(rates)
    sell = find_best_sell(rates)

    print("Best buy :", f"{buy.name:<20} S/ {buy.buy_price:.4f}")
    print("Best sell:", f"{sell.name:<20} S/ {sell.sell_price:.4f}")
    print()


async def top_five():
    """Rank the five cheapest places to buy and the five best places to sell."""
    rates = await fetch_rates()

    print("Top 5 BUY")
    for i, r in enumerate(get_top_n(rates, 5, "buy"), 1):
        print(f"  {i}. {r.name:<20} S/ {r.buy_price:.4f}")

    print("\nTop 5 SELL")
    for i, r in enumerate(get_top_n(rates, 5, "sell"), 1):
        print(f"  {i}. {r.name:<20} S/ {r.sell_price:.4f}")

    print()


async def market_stats():
    """Print simple market statistics."""
    rates = await fetch_rates()

    print("Market snapshot")
    print(f"  Exchange houses: {len(rates)}")
    print(f"  Avg buy : S/ {calculate_average(rates, 'buy'):.4f}")
    print(f"  Avg sell: S/ {calculate_average(rates, 'sell'):.4f}")
    print(f"  Avg spread: S/ {calculate_spread(rates):.4f}")
    print()


async def low_spread():
    """List the five exchanges with the tightest spreads."""
    rates = await fetch_rates()

    print("Lowest spreads")
    for r in sorted(rates, key=lambda x: x.spread)[:5]:
        print(f"  {r.name:<20} spread S/ {r.spread:.4f}")
    print()


async def export_json():
    """Save current rates to exchange_rates.json."""
    rates = await fetch_rates()

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rates": [
            {
                "name": r.name,
                "buy": r.buy_price,
                "sell": r.sell_price,
                "spread": r.spread,
            }
            for r in rates
        ],
    }

    with pathlib.Path("exchange_rates.json").open("w") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved {len(rates)} records to exchange_rates.json")
    print()


async def main():
    print("perexchange quick-start examples\n")

    await best_prices()
    await top_five()
    await market_stats()
    await low_spread()
    await export_json()


if __name__ == "__main__":
    asyncio.run(main())
