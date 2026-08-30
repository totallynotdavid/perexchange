import asyncio
import sys

import httpx

from perexchange import fetch_rates_report


def print_separator() -> None:
    print("=" * 60)


async def cmd_fetch() -> None:
    print("Fetching current exchange rates...")
    report = await fetch_rates_report()
    rates = report.rates

    for failure in report.failures:
        print(f"Skipped {failure.source}: {failure.message}", file=sys.stderr)

    print_separator()
    print(f"CURRENT EXCHANGE RATES ({len(rates)} rates)")
    print_separator()

    for rate in sorted(rates, key=lambda r: r.buy_price):
        print(f"{rate.name} ({rate.source}):")
        print(f"  Buy:  S/ {rate.buy_price:.4f}")
        print(f"  Sell: S/ {rate.sell_price:.4f}")
        print(f"  Spread: S/ {rate.spread:.4f}")
        print()


def print_help() -> None:
    print("perexchange: peruvian exchange rate tool (dev/local use only)")
    print("\nUsage: perexchange [command]")
    print("\nCommands:")
    print("  fetch       - Fetch and display all current rates")
    print("  help        - Show this help message")


async def run_command(command: str | None = None) -> None:
    if command is None or command == "help" or command == "--help" or command == "-h":
        print_help()
        return

    try:
        if command == "fetch":
            await cmd_fetch()
        else:
            print(f"Unknown command: {command}")
            print("Run 'perexchange help' for usage information.")
            sys.exit(1)

    except (httpx.HTTPError, ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        asyncio.run(run_command(command))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
