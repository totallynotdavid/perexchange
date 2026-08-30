# perexchange

[![CodeQL](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml)
[![tests](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/perexchange/graph/badge.svg?token=KYQVD9QU30)](https://codecov.io/gh/totallynotdavid/perexchange)

Fetch PEN/USD exchange rates from registered Peruvian exchange houses.

Python 3.10 or newer is required.

## Install

```bash
pip install perexchange
```

## Get started

`fetch_rates()` queries the registered sources concurrently and returns the rates that
were fetched successfully.

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

## Documentation

Read the [core API reference](packages/core/readme.md) for the complete signature, result
ordering, retry behavior, and error handling. The [examples](examples.py) cover targeted
fetching, tiered rates, spreads, caching, and market summaries.

The [CLI](packages/cli/readme.md) is a local diagnostic tool and is not part of the
published library.

## Development

The repository uses `mise` for tasks and `uv` for dependencies:

```bash
mise run sync
mise run test
mise run check
```

`mise run check` only verifies formatting, types, and tests. Use `mise run format` and
`mise run format-docs` to rewrite files.

Integration tests call the live exchange-house endpoints and can be slow or flaky. Run
them separately:

```bash
mise run test-integration
```

See [contributing](.github/CONTRIBUTING.md) and the
[architecture notes](docs/architecture.md) before changing a scraper.
