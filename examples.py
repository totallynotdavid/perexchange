"""
Quick-start examples. Just run: python examples.py (or uv run python examples.py)
"""

import asyncio
import json
from datetime import datetime
from perexchange import (
    fetch_rates,
    find_best_buy,
    find_best_sell,
    get_top_n,
    calculate_average,
    calculate_spread,
)


async def best_prices():
    """Show the best buy and sell prices right now."""
    rates = await fetch_rates()

    buy = find_best_buy(rates)
    sell = find_best_sell(rates)

    print("Best buy :", f"{buy.name:<20} S/ {buy.buy_price}")
    print("Best sell:", f"{sell.name:<20} S/ {sell.sell_price}")
    print()


async def top_three():
    """Rank the three cheapest places to buy and the three best places to sell."""
    rates = await fetch_rates()

    print("Top 3 BUY")
    for i, r in enumerate(get_top_n(rates, 3, "buy"), 1):
        print(f"  {i}. {r.name:<20} S/ {r.buy_price}")

    print("\nTop 3 SELL")
    for i, r in enumerate(get_top_n(rates, 3, "sell"), 1):
        print(f"  {i}. {r.name:<20} S/ {r.sell_price}")

    print()


async def stats():
    """Print simple market statistics."""
    rates = await fetch_rates()

    print("Market snapshot")
    print("  Avg buy : S/ ", calculate_average(rates, "buy"))
    print("  Avg sell: S/ ", calculate_average(rates, "sell"))
    print("  Spread  : S/ ", calculate_spread(rates))
    print()


async def low_spread():
    """List the five exchanges with the tightest spreads."""
    rates = await fetch_rates()

    print("Lowest spreads")
    for r in sorted(rates, key=lambda x: x.spread)[:5]:
        print(f"  {r.name:<20} spread S/ {r.spread}")
    print()


async def dump_json():
    """Save current rates to exchange_rates.json."""
    rates = await fetch_rates()

    payload = {
        "timestamp": datetime.utcnow().isoformat(),
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

    with open("exchange_rates.json", "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved {len(rates)} records to exchange_rates.json")
    print()


async def poll():
    """Poll every 10 s for 30 s and print the best buy price."""
    import time

    stop = time.time() + 30
    while time.time() < stop:
        rates = await fetch_rates()
        best = find_best_buy(rates)
        print(datetime.now().strftime("%H:%M:%S"), "-", best.name, "S/", best.buy_price)
        await asyncio.sleep(10)


async def main():
    print("perexchange quick-start\n")

    await best_prices()
    await top_three()
    await stats()
    await low_spread()
    await dump_json()

    # Uncomment to see the polling demo
    # await poll()


if __name__ == "__main__":
    asyncio.run(main())
