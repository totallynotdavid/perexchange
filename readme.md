# [monorepo]: perexchange

[![CodeQL](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml)
[![tests](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/perexchange/graph/badge.svg?token=KYQVD9QU30)](https://codecov.io/gh/totallynotdavid/perexchange)

A minimal library for fetching PEN-USD exchange rates from Peruvian exchange houses.

To install the library, run:

```bash
pip install perexchange
```

## Quick start

The library fetches rates from multiple sources concurrently and returns them as a list.

Find the best rate by sorting:

```python
import asyncio
import perexchange as px

async def main():
    rates = await px.fetch_rates()
    best = min(rates, key=lambda r: r.buy_price)
    print(f"{best.name}: S/{best.buy_price}")

asyncio.run(main())
```

See [examples.py](examples.py) for more usage patterns.

## Documentation

The core API consists of one function and one data model. Call `fetch_rates()` to retrieve
current rates from all available sources, or pass a list of specific house names. The
function returns `ExchangeRate` objects containing prices, timestamps, and metadata.

Read the full API documentation in [pkg/core/readme.md](pkg/core/readme.md).

## Development

This is a monorepo containing the core library under `pkg/core/`. The project uses mise
for task management and uv for dependency management. Common tasks:

```bash
mise run sync        # install dependencies
mise run test        # run unit tests
mise run format      # format and lint
mise run pre-push    # quick checks before pushing
```

The test suite includes unit tests with fixtures and integration tests that hit live APIs.
Integration tests are slower and can be flaky. Run them separately:

```bash
mise run test-integration
```

Contributing guidelines and repository structure details are in
[CONTRIBUTING](.github/CONTRIBUTING.md).
