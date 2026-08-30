# perexchange

[![CodeQL](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml)
[![tests](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/perexchange/graph/badge.svg?token=KYQVD9QU30)](https://codecov.io/gh/totallynotdavid/perexchange)

Fetch live PEN/USD exchange rates from Peruvian exchange houses.

Requires Python 3.10 or later.

## Get started

```bash
python -m pip install perexchange
```

`fetch_rates()` is asynchronous. It queries the registered sources at the same time and
returns the rates that succeeded. Each rate has a stable `source` ID and a display `name`.

```python
import asyncio

import perexchange


async def main() -> None:
    rates = await perexchange.fetch_rates()
    if not rates:
        print("No rates available")
        return

    best = min(rates, key=lambda rate: rate.buy_price)
    print(f"{best.source}: S/{best.buy_price:.4f}")


asyncio.run(main())
```

## Read more

- [API reference](packages/core/README.md) for request options, retries, ordering, and
  errors.
- [Examples](examples.py) for selecting sources, comparing tiers, measuring spreads,
  caching, and summarizing the market. Run them with `uv run python examples.py`.
- [Architecture notes](docs/architecture.md) for the fetch path and adapter boundary.
- [CLI](packages/cli/readme.md) for the local development command.
- [Release process](docs/releasing.md) for publishing the core package to PyPI.

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
checking, unit tests, and package artifact checks. Live integration tests call
exchange-house endpoints and are separate because they can be slow or fail when a site
rate-limits the requests:

```bash
mise run test-integration
```

See [contributing](.github/CONTRIBUTING.md) before changing an adapter.
