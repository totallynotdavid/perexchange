# perexchange

[![CodeQL](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml)
[![tests](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/perexchange/graph/badge.svg?token=KYQVD9QU30)](https://codecov.io/gh/totallynotdavid/perexchange)

Fetch live PEN/USD exchange rates from Peruvian exchange houses.

## Get started

You need Python 3.10 or later.

Install the library:

```bash
pip install perexchange
```

`fetch_rates()` is asynchronous. It queries the registered houses at the same time and
returns the rates that succeeded.

```python
import asyncio

import perexchange as px


async def main() -> None:
    rates = await px.fetch_rates()
    if not rates:
        print("No rates available")
        return

    best = min(rates, key=lambda rate: rate.buy_price)
    print(f"{best.name}: S/{best.buy_price:.4f}")


asyncio.run(main())
```

## Read more

- [API reference](packages/core/readme.md) for request options, retries, ordering, and
  errors.
- [Examples](examples.py) for selecting houses, comparing tiers, measuring spreads,
  caching, and summarizing the market. Run them with `uv run python examples.py`.
- [Architecture notes](docs/architecture.md) for the fetch path and scraper boundary.
- [CLI](packages/cli/readme.md) for the local development command.

## Develop

Install the workspace dependencies with:

```bash
mise run sync
```

Run the default checks with:

```bash
mise run check
```

The check task runs Python formatting and linting, Markdown and YAML formatting, type
checking, and unit tests. Live integration tests call exchange-house endpoints and are
separate because they can be slow or fail when a site rate-limits the requests:

```bash
mise run test-integration
```

See [contributing](.github/CONTRIBUTING.md) before changing a scraper.
