# perexchange

[![CodeQL](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml)
[![tests](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/perexchange/graph/badge.svg?token=KYQVD9QU30)](https://codecov.io/gh/totallynotdavid/perexchange)

perexchange is an asynchronous Python library that fetches live PEN/USD exchange rates
from Peruvian exchange houses. It queries every house at once, needs no API key, and
returns the rates that arrived. A house that fails is left out and reported.

It reads the public pages and endpoints of each house, so it returns what they publish and
nothing else: PEN/USD only, with no history. Requires Python 3.10 or later.

## Get started

```bash
python -m pip install perexchange
```

Find the cheapest place to buy a dollar:

```python
import asyncio

import perexchange


async def main() -> None:
    rates = await perexchange.fetch_rates()
    if not rates:
        print("No rates available")
        return

    cheapest = min(rates, key=lambda rate: rate.sell_price)
    print(f"{cheapest.name}: S/{cheapest.sell_price:.4f} per USD")


asyncio.run(main())
```

```text
mercadocambiario: S/3.4410 per USD
```

`buy_price` is what the house pays you for a dollar. `sell_price` is what it charges. See
the [API reference](docs/api.md) for every field.

## Features

- Fetches all sources concurrently, or the ones you name.
- Retries transport errors and temporary HTTP responses with backoff, and honors
  `Retry-After`.
- Limits each request and each source with separate timeouts.
- Reports which sources failed and why, through `fetch_rates_report()`.
- Reuses your `httpx.AsyncClient` when you pass one.
- Returns immutable `ExchangeRate` values with timezone-aware timestamps.

## Learn more

- [Manual](docs/README.md): the API reference, the CLI, how a fetch works, and how
  releases are made.
- [Examples](examples): list every rate, find the best rates to buy and sell, summarize
  the market, and cache results. Run one with `uv run python examples/best_rates.py`.
- [Site](site/README.md): the rates site at <https://perexchange.vercel.app>, its open
  data, and how it is built and deployed.
- [Contributing](.github/CONTRIBUTING.md): set up, run the checks, and add a source.
