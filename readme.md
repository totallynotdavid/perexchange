# [monorepo]: perexchange

[![CodeQL](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml)
[![tests](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/perexchange/graph/badge.svg?token=KYQVD9QU30)](https://codecov.io/gh/totallynotdavid/perexchange)

A minimal library for retrieving PEN–USD exchange rates from multiple Peruvian exchange
houses.

This repository is a monorepo containing two packages:

1. Core library (published to PyPI)
2. Optional CLI tool (development only)

To install the library, run:

```
pip install perexchange
```

Quick usage example:

```python
import asyncio, perexchange as px

rates = await px.fetch_rates()
px.find_best_buy(rates)
```

<!-- prettier-ignore -->
> [!TIP]
> See more complex examples on [examples.py](examples.py).

The core API includes functions for fetching rates, selecting the best buy and sell
prices, and working with the ExchangeRate data model.

For detailed API documentation, see [pkg/core/readme.md](pkg/core/readme.md).

The CLI tool exists for development and inspection only. For CLI details, see
[pkg/cli/readme.md](pkg/cli/readme.md).

For development workflow, testing instructions, adding scrapers, and repository structure,
refer to [CONTRIBUTING](.github/CONTRIBUTING.md).
