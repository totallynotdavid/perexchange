# ruff: file-ignore[implicit-namespace-package]
"""Summarize the market: the tightest spreads and the range of prices.

Run from the repository root: `uv run python examples/market.py`. The script makes
live requests.
"""

import asyncio

from statistics import mean

import httpx
import perexchange

from perexchange import ExchangeRate


def tightest_spreads(rates: list[ExchangeRate], count: int = 5) -> list[ExchangeRate]:
    return sorted(rates, key=lambda rate: rate.spread)[:count]


async def main(client: httpx.AsyncClient | None = None) -> None:
    rates = await perexchange.fetch_rates(client=client)
    if not rates:
        print("No rates available")
        return

    print("Tightest spreads:")
    for rate in tightest_spreads(rates):
        share = rate.spread / rate.sell_price * 100
        print(f"{rate.source}/{rate.name}: S/{rate.spread:.4f} ({share:.2f}%)")

    paid = [rate.buy_price for rate in rates]
    charged = [rate.sell_price for rate in rates]
    houses = len({rate.source for rate in rates})
    print(f"\n{len(rates)} quotes from {houses} sources")
    print(
        f"Houses pay S/{min(paid):.4f} to S/{max(paid):.4f}, on average {mean(paid):.4f}"
    )
    print(
        f"Houses charge S/{min(charged):.4f} to S/{max(charged):.4f}, "
        f"on average {mean(charged):.4f}"
    )


if __name__ == "__main__":
    asyncio.run(main())
