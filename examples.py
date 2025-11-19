"""
Quick-start examples. Run: python examples.py (or uv run python examples.py)
"""

import asyncio
import json
import pathlib

from datetime import datetime, timedelta, timezone

import perexchange as px


async def basic_usage():
    """Fetch rates from all available sources."""
    rates = await px.fetch_rates()

    print(f"Fetched {len(rates)} rates")
    for rate in rates[:5]:
        print(f"{rate.name}: buy S/{rate.buy_price:.4f}, sell S/{rate.sell_price:.4f}")

    if rates:
        data = []
        for rate in rates:
            rate_dict = {
                "name": rate.name,
                "buy_price": rate.buy_price,
                "sell_price": rate.sell_price,
                "timestamp": rate.timestamp.isoformat(),
            }
            data.append(rate_dict)
        with pathlib.Path("rates.json").open("w") as f:
            json.dump(data, f, indent=2)
        print("Saved rates to rates.json")


async def targeted_fetching():
    """Fetch from specific houses."""
    fast_houses = ["tkambio", "tucambista"]
    rates = await px.fetch_rates(houses=fast_houses, timeout=5.0)

    for rate in rates:
        print(f"{rate.name}: S/{rate.buy_price:.4f}")


async def find_best_rates():
    """Find the best buy and sell rates across all sources."""
    rates = await px.fetch_rates()

    if not rates:
        print("No rates available")
        return

    best_buy = min(rates, key=lambda r: r.buy_price)
    best_sell = max(rates, key=lambda r: r.sell_price)

    print(f"Best buy: {best_buy.name} at S/{best_buy.buy_price:.4f}")
    print(f"Best sell: {best_sell.name} at S/{best_sell.sell_price:.4f}")

    arbitrage = best_sell.sell_price - best_buy.buy_price
    if arbitrage > 0:
        print(f"Arbitrage opportunity: S/{arbitrage:.4f} per dollar")


async def analyze_spreads():
    """Find houses with the tightest bid-ask spreads."""
    rates = await px.fetch_rates()

    if not rates:
        print("No rates available")
        return

    sorted_by_spread = sorted(rates, key=lambda r: r.spread)

    print("Tightest spreads:")
    for rate in sorted_by_spread[:5]:
        percentage = (rate.spread / rate.buy_price) * 100
        print(f"{rate.name}: S/{rate.spread:.4f} ({percentage:.2f}%)")


async def working_with_tiers():
    """Filter and compare tiered rates for bulk transactions."""
    rates = await px.fetch_rates()

    base_rates = [r for r in rates if "_" not in r.name]
    tiered_rates = [r for r in rates if "_" in r.name]

    print(f"Base rates: {len(base_rates)}")
    print(f"Tiered rates: {len(tiered_rates)}")

    if tiered_rates:
        print("\nBest rates by tier:")
        tiers = {}
        for rate in tiered_rates:
            _house, tier = rate.name.split("_", 1)
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(rate)

        for tier, tier_rates in sorted(tiers.items()):
            best = min(tier_rates, key=lambda r: r.buy_price)
            print(f"${tier}+: {best.name} at S/{best.buy_price:.4f}")


async def simple_caching():
    """Cache results to avoid redundant API calls. Users must implement their own caching logic."""
    cache = {"rates": None, "timestamp": None}
    cache_duration = timedelta(minutes=5)

    async def get_rates_cached():
        now = datetime.now(timezone.utc)

        if cache["rates"] and cache["timestamp"]:
            age = now - cache["timestamp"]
            if age < cache_duration:
                print(f"Cache hit (age: {age.seconds}s)")
                return cache["rates"]

        print("Cache miss, fetching")
        rates = await px.fetch_rates()
        cache["rates"] = rates
        cache["timestamp"] = now
        return rates

    rates1 = await get_rates_cached()
    print(f"First call: {len(rates1)} rates")

    await asyncio.sleep(2)

    rates2 = await get_rates_cached()
    print(f"Second call: {len(rates2)} rates")


async def market_overview():
    """Calculate market statistics across all sources."""
    rates = await px.fetch_rates()

    if not rates:
        print("No rates available")
        return

    buy_prices = [r.buy_price for r in rates]
    sell_prices = [r.sell_price for r in rates]
    spreads = [r.spread for r in rates]

    sources = len({r.name.split("_")[0] for r in rates})

    print(f"Market snapshot from {sources} sources:")
    print(f"Buy range: S/{min(buy_prices):.4f} - S/{max(buy_prices):.4f}")
    print(f"Sell range: S/{min(sell_prices):.4f} - S/{max(sell_prices):.4f}")
    print(f"Average buy: S/{sum(buy_prices) / len(buy_prices):.4f}")
    print(f"Average sell: S/{sum(sell_prices) / len(sell_prices):.4f}")
    print(f"Average spread: S/{sum(spreads) / len(spreads):.4f}")


async def main():
    examples = [
        ("Basic usage", basic_usage),
        ("Find best rates", find_best_rates),
        ("Analyze spreads", analyze_spreads),
        ("Working with tiers", working_with_tiers),
        ("Simple caching", simple_caching),
        ("Market overview", market_overview),
    ]

    for name, func in examples:
        print(f"\n{'=' * 60}")
        print(f"{name}")
        print("=" * 60)
        try:
            await func()
        except Exception as e:  # noqa: BLE001 (broad Exception to handle any errors in examples without crashing)
            print(f"Error: {e}")
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
