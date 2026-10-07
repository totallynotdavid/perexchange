# ruff: file-ignore[implicit-namespace-package]
"""Fetch rates from all sources and list the ones that failed.

Run from the repository root: `uv run python examples/basic.py`. The script makes live
requests.
"""

import asyncio

import httpx
import perexchange


async def main(client: httpx.AsyncClient | None = None) -> None:
    report = await perexchange.fetch_rates_report(client=client)

    print(f"Fetched {len(report.rates)} rates")
    for rate in report.rates:
        print(
            f"{rate.source}/{rate.name}: "
            f"pays S/{rate.buy_price:.4f}, charges S/{rate.sell_price:.4f}"
        )

    for failure in report.failures:
        print(f"Failed {failure.source}: {failure.error_type}: {failure.message}")


if __name__ == "__main__":
    asyncio.run(main())
