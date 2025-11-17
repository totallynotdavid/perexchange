import asyncio
import sys

import httpx

from perexchange import (
    calculate_average,
    calculate_spread,
    fetch_rates,
    find_best_buy,
    find_best_sell,
)
from perexchange.analysis import get_top_n


def print_separator():
    print("=" * 60)


async def cmd_fetch():
    print("Fetching current exchange rates...")
    rates = await fetch_rates()

    print_separator()
    print(f"CURRENT EXCHANGE RATES ({len(rates)} houses)")
    print_separator()

    for rate in sorted(rates, key=lambda r: r.buy_price):
        print(f"{rate.name}:")
        print(f"  Buy:  S/ {rate.buy_price:.4f}")
        print(f"  Sell: S/ {rate.sell_price:.4f}")
        print(f"  Spread: S/ {rate.spread:.4f}")
        print()


async def cmd_best_buy():
    print("Finding best place to buy dollars...")
    rates = await fetch_rates()
    best = find_best_buy(rates)

    if best:
        print_separator()
        print("BEST PLACE TO BUY DOLLARS")
        print_separator()
        print(f"Exchange House: {best.name}")
        print(f"Buy Price: S/ {best.buy_price:.4f}")
        print(f"Timestamp: {best.timestamp}")
        print_separator()
    else:
        print("No rates available.")


async def cmd_best_sell():
    print("Finding best place to sell dollars...")
    rates = await fetch_rates()
    best = find_best_sell(rates)

    if best:
        print_separator()
        print("BEST PLACE TO SELL DOLLARS")
        print_separator()
        print(f"Exchange House: {best.name}")
        print(f"Sell Price: S/ {best.sell_price:.4f}")
        print(f"Timestamp: {best.timestamp}")
        print_separator()
    else:
        print("No rates available.")


async def cmd_top(n: int = 5, operation: str = "buy"):
    print(f"Finding top {n} places to {operation}...")
    rates = await fetch_rates()
    top = get_top_n(rates, n=n, operation=operation)

    if top:
        print_separator()
        print(f"TOP {n} PLACES TO {operation.upper()} DOLLARS")
        print_separator()
        for i, rate in enumerate(top, 1):
            price = rate.buy_price if operation == "buy" else rate.sell_price
            print(f"{i}. {rate.name}: S/ {price:.4f}")
        print_separator()
    else:
        print("No rates available.")


async def cmd_stats():
    print("Calculating statistics...")
    rates = await fetch_rates()

    avg_buy = calculate_average(rates, operation="buy")
    avg_sell = calculate_average(rates, operation="sell")
    avg_spread = calculate_spread(rates)

    print_separator()
    print("STATISTICS")
    print_separator()
    print(f"Exchange Houses: {len(rates)}")
    print(f"Average Buy Price: S/ {avg_buy:.4f}")
    print(f"Average Sell Price: S/ {avg_sell:.4f}")
    print(f"Average Spread: S/ {avg_spread:.4f}")

    best_buy = find_best_buy(rates)
    best_sell = find_best_sell(rates)

    print(f"\nBest Buy: {best_buy.name} (S/ {best_buy.buy_price:.4f})")
    print(f"Best Sell: {best_sell.name} (S/ {best_sell.sell_price:.4f})")
    print_separator()


def print_help():
    print("perexchange: peruvian exchange rate tool")
    print("\nUsage: perexchange [command]")
    print("\nCommands:")
    print("  fetch       - Fetch and display all current rates")
    print("  best-buy    - Show best place to buy dollars")
    print("  best-sell   - Show best place to sell dollars")
    print("  top-buy     - Show top 5 places to buy")
    print("  top-sell    - Show top 5 places to sell")
    print("  stats       - Show statistics and analysis")
    print("  help        - Show this help message")
    print("\nExamples:")
    print("  perexchange best-buy")
    print("  perexchange top-sell")


async def run_command(command: str | None = None):
    if command is None or command == "help" or command == "--help" or command == "-h":
        print_help()
        return

    try:
        if command == "fetch":
            await cmd_fetch()
        elif command == "best-buy":
            await cmd_best_buy()
        elif command == "best-sell":
            await cmd_best_sell()
        elif command == "top-buy":
            await cmd_top(n=5, operation="buy")
        elif command == "top-sell":
            await cmd_top(n=5, operation="sell")
        elif command == "stats":
            await cmd_stats()
        else:
            print(f"Unknown command: {command}")
            print("Run 'perexchange help' for usage information.")
            sys.exit(1)

    except (httpx.HTTPError, ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        asyncio.run(run_command(command))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
