# ruff: file-ignore[implicit-namespace-package]
"""Find where to buy dollars cheapest and where to sell them for the most.

Run from the repository root: `uv run python examples/best_rates.py`. The script makes
live requests.
"""

import asyncio

import httpx
import perexchange

from perexchange import ExchangeRate


def cheapest_to_buy(rates: list[ExchangeRate]) -> ExchangeRate:
    """The quote that charges the least for a dollar."""
    return min(rates, key=lambda rate: rate.sell_price)


def best_to_sell(rates: list[ExchangeRate]) -> ExchangeRate:
    """The quote that pays the most for a dollar."""
    return max(rates, key=lambda rate: rate.buy_price)


def arbitrage_per_dollar(rates: list[ExchangeRate]) -> float:
    """Profit from buying at the cheapest quote and selling at the best one.

    The result is negative when no pair of quotes allows a profit.
    """
    return best_to_sell(rates).buy_price - cheapest_to_buy(rates).sell_price


def group_by_tier(rates: list[ExchangeRate]) -> dict[int, list[ExchangeRate]]:
    """Group quotes by the minimum amount in USD, as in `tkambio_5000`.

    Quotes without an amount in their name are left out.
    """
    tiers: dict[int, list[ExchangeRate]] = {}
    for rate in rates:
        _, _, suffix = rate.name.rpartition("_")
        if suffix.isdigit():
            tiers.setdefault(int(suffix), []).append(rate)
    return tiers


async def main(client: httpx.AsyncClient | None = None) -> None:
    rates = await perexchange.fetch_rates(client=client)
    if not rates:
        print("No rates available")
        return

    buy = cheapest_to_buy(rates)
    sell = best_to_sell(rates)
    print(f"Cheapest to buy: {buy.source}/{buy.name} charges S/{buy.sell_price:.4f}")
    print(f"Best to sell: {sell.source}/{sell.name} pays S/{sell.buy_price:.4f}")

    profit = arbitrage_per_dollar(rates)
    if profit > 0:
        print(f"Arbitrage: S/{profit:.4f} per dollar")
    else:
        print(f"No arbitrage: the best sale is S/{-profit:.4f} below the cheapest buy")

    for amount, tier_rates in sorted(group_by_tier(rates).items()):
        buy = cheapest_to_buy(tier_rates)
        sell = best_to_sell(tier_rates)
        print(
            f"${amount}+: buy at {buy.name} for S/{buy.sell_price:.4f}, "
            f"sell at {sell.name} for S/{sell.buy_price:.4f}"
        )


if __name__ == "__main__":
    asyncio.run(main())
