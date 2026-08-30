# perexchange

The core package fetches live PEN/USD exchange rates from registered Peruvian exchange
houses.

## Install

You need Python 3.10 or later. Install the published package with:

```bash
pip install perexchange
```

## First call

`fetch_rates()` is asynchronous and returns a list of `ExchangeRate` objects.

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

## `fetch_rates`

```python
async def fetch_rates(
    houses: Sequence[str] | None = None,
    *,
    timeout: float = 10.0,
    max_retries: int = 3,
    client: httpx.AsyncClient | None = None,
) -> list[ExchangeRate]:
```

### Choose houses

With no `houses` argument, the function queries every house in the registry. Pass names to
query only a subset:

```python
rates = await px.fetch_rates(houses=["tkambio", "tucambista"])
```

House names are matched without regard to case. An unknown name raises `ValueError` before
the first request and includes the accepted names in the error message.

### Timeouts and retries

- `timeout` applies to each HTTP request.
- `max_retries` is the total number of calls to each scraper, including the first call.
- Transport errors and `408`, `429`, and `5xx` responses may be retried.
- Other `4xx` responses and parsing errors are not retried.
- Retry delays use exponential backoff. A numeric `Retry-After` value for `429` wins and
  is capped at 30 seconds.

Some scrapers make more than one request. A retry repeats that scraper's whole operation,
including requests that already succeeded.

Pass an existing `httpx.AsyncClient` when polling repeatedly so it can reuse connections.
`fetch_rates()` leaves a passed client open. If you omit `client`, the function creates a
client for the call and closes it before returning.

### Failures and ordering

An expected transport or parsing failure affects only that house. The failed rate is left
out and a warning is written to the `perexchange` logger. Inspect that logger when you
need to know why a source was left out. If no selected house returns a rate, the function
returns an empty list. Other exceptions are allowed to propagate.

Results preserve the selected-house order. When `houses` is omitted, that is registry
order. If multiple scrapers return the same rate name, the first result wins.

## `ExchangeRate`

Each result is a frozen dataclass with these fields:

- `name`: the house or quote name. A name can include a transaction tier, such as
  `tkambio_5000`.
- `buy_price`: PEN needed to buy one USD.
- `sell_price`: PEN received for selling one USD.
- `timestamp`: a timezone-aware `datetime` supplied by the scraper. It may be the source's
  update time or the time the response was fetched.

The `spread` property is `sell_price - buy_price`, in PEN per USD:

```python
rate = rates[0]
print(rate.name, rate.buy_price, rate.sell_price, rate.spread)
```

Some houses return several quotes. Tier suffixes are part of the returned rate name; they
are not names that can be passed to `fetch_rates()`.

Find the lowest price for buying USD or the highest price for selling it with:

```python
best_buy = min(rates, key=lambda rate: rate.buy_price)
best_sell = max(rates, key=lambda rate: rate.sell_price)
```

The result list does not carry the failure reason. A source can be unavailable, return a
response the parser does not recognize, or change its API.
