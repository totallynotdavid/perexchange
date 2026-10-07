# perexchange

perexchange is an asynchronous Python library that fetches live PEN/USD exchange rates
from Peruvian exchange houses. It queries the houses concurrently and returns the rates
that arrived. It needs no API key and requires Python 3.10 or later.

## Install

```bash
python -m pip install perexchange
```

## Fetch rates

```python
import asyncio

import perexchange


async def main() -> None:
    report = await perexchange.fetch_rates_report()

    for failure in report.failures:
        print(f"{failure.source} failed: {failure.message}")

    if report.rates:
        cheapest = min(report.rates, key=lambda rate: rate.sell_price)
        print(f"{cheapest.source} charges S/{cheapest.sell_price} for a dollar")


asyncio.run(main())
```

Each `ExchangeRate` has a `buy_price`, what the house pays you for a dollar, and a
`sell_price`, what it charges you. A source that fails is listed in `report.failures` and
does not stop the others.

## Learn more

[API reference](https://github.com/totallynotdavid/perexchange/blob/master/docs/api.md)
covers source selection, fetch settings, retries, failures and the data classes. The
[repository](https://github.com/totallynotdavid/perexchange) has the issue tracker and the
contributing guide.
