# perexchange API

Fetch PEN/USD exchange rates from registered Peruvian exchange houses.

Requires Python 3.10 or newer.

Install the published package with:

```bash
pip install perexchange
```

## API

### `fetch_rates`

```python
async def fetch_rates(
    houses: Sequence[str] | None = None,
    *,
    timeout: float = 10.0,
    max_retries: int = 3,
    client: httpx.AsyncClient | None = None,
) -> list[ExchangeRate]:
```

The function queries the selected exchange-house adapters concurrently.

```python
import asyncio
import perexchange as px


async def main():
    rates = await px.fetch_rates()
    if not rates:
        print("No rates available")
        return

    best = min(rates, key=lambda r: r.buy_price)
    print(f"{best.name}: S/{best.buy_price:.4f}")


asyncio.run(main())
```

## Fetching rates

With no `houses` argument, the function queries every source registered by the package.
The [registry](perexchange/scrapers/registry.py) owns the accepted house names. An unknown
name raises `ValueError` before any request is made and includes the available names in
the error message.

The examples below assume they run inside an async function.

Pass house names to limit the query:

```python
rates = await px.fetch_rates(houses=["tkambio", "tucambista"])
```

`timeout` applies to each HTTP request. `max_retries` limits calls to each scraper's fetch
operation, including the first call. A simple scraper makes one request per call;
multi-request scrapers can make more than one request and repeat earlier requests when a
later request fails. Transport errors and temporary HTTP responses (`408`, `429`, and
`5xx`) may be retried; parsing errors are not retried. Retry delays use exponential
backoff and honor a numeric `Retry-After` value for `429` responses, capped at 30 seconds.

Pass an existing `httpx.AsyncClient` as `client` when polling repeatedly to reuse
connections. The caller owns that client's lifecycle.

```python
rates = await px.fetch_rates(timeout=15.0, max_retries=5)
```

Expected transport and parsing failures are isolated per source, omitted from the returned
list, and logged as warnings through the `perexchange` logger. The function returns an
empty list when no selected source produces a rate. Unexpected exceptions are not
converted into a partial result.

Results follow the selected-house order. When `houses` is omitted, that is registry order.
If multiple adapters return the same rate name, the first adapter in that order wins.

## Working with rates

Each returned `ExchangeRate` is a frozen dataclass containing a rate name, two PEN/USD
prices, and a UTC-aware timestamp. `buy_price` is the amount of soles needed to buy one
USD; `sell_price` is the amount received for selling one USD.

```python
rate = rates[0]
name = rate.name
buy = rate.buy_price
sell = rate.sell_price
when = rate.timestamp
spread = rate.spread
```

`spread` is `sell_price - buy_price`. Some sources return multiple rates for transaction
tiers, such as `tkambio_5000` and `tkambio_10000`; those suffixes are rate names, not
house names accepted by `fetch_rates()`.

Find the best rates by sorting or filtering the list:

```python
best_buy = min(rates, key=lambda r: r.buy_price)
best_sell = max(rates, key=lambda r: r.sell_price)
```

The timestamp is supplied by each adapter. It may be the source's update time or the time
the response was fetched.

## Errors and unavailable sources

For expected source failures, inspect the `perexchange` log when the reason matters:

Inside an async function:

```python
try:
    rates = await px.fetch_rates(houses=["nonexistent"])
except ValueError as e:
    print(f"Unknown house: {e}")

rates = await px.fetch_rates()
if not rates:
    print("All sources failed")
```

A source can fail because of a network problem, an API change, or a parsing error. The
return type does not distinguish those causes.
