# perexchange

`perexchange` fetches live PEN/USD rates from Peruvian exchange houses.

Requires Python 3.10 or later.

## Install

```bash
python -m pip install perexchange
```

## Fetch rates

`fetch_rates()` runs the selected source adapters concurrently and returns the rates that
were fetched successfully:

```python
import asyncio

import perexchange


async def main() -> None:
    rates = await perexchange.fetch_rates(sources=["cambiafx", "tucambista"])
    for rate in rates:
        print(rate.source, rate.name, rate.buy_price, rate.sell_price)


asyncio.run(main())
```

With no `sources` argument, all registered sources are queried. Source names are matched
without regard to case, accents, spaces, or punctuation. `kambioonline2` is an alias for
`kambioonline`.

An unknown or repeated source raises `ConfigurationError` before any request starts.
Invalid timeout and retry settings raise the same exception.

## Fetch settings

```python
async def fetch_rates(
    sources: Sequence[str] | None = None,
    *,
    timeout: float = 10.0,
    max_attempts: int = 3,
    total_timeout: float | None = 30.0,
    client: httpx.AsyncClient | None = None,
) -> list[ExchangeRate]:
```

- `timeout` limits each HTTP request.
- `max_attempts` is the total number of attempts for each source, including the first.
- `total_timeout` limits one source operation, including retries and backoff. Set it to
  `None` to disable that limit.
- Transport errors and `408`, `429`, and `5xx` responses are retried. Other `4xx`
  responses and parse errors are not.
- A numeric `Retry-After` value for `429` is honored up to 30 seconds.
- If you pass a client, `perexchange` leaves it open. Otherwise it creates and closes a
  client for the call.

Some sources need more than one request. One attempt repeats that source's full operation.

## Failures

`fetch_rates()` leaves sources that fail out of its result. Use `fetch_rates_report()`
when the caller needs to distinguish an empty result from sources that failed:

```python
report = await perexchange.fetch_rates_report()

for failure in report.failures:
    print(f"{failure.source}: {failure.message}")
```

Expected network, timeout, and parse failures are recorded in `report.failures`. Other
exceptions are raised so programming errors are not hidden.

`ConfigurationError` is available from the top-level `perexchange` module for callers that
need to catch invalid source selections or fetch settings.

Results keep source selection order. A repeated `(source, name)` pair keeps its first
value. The aggregator's rows for sources with a dedicated adapter are removed from the
final result.

## Version 2.0 changes

- `ExchangeRate` requires a `source` field.
- `fetch_rates()` and `fetch_rates_report()` use `sources` instead of `houses`.
- `max_retries` is now `max_attempts`.
- Source failures are available through `fetch_rates_report()`.

## `ExchangeRate`

`ExchangeRate` is an immutable dataclass with these fields:

- `source`: the stable source ID, such as `cambiafx`.
- `name`: the display name returned by the source. It can include a quote tier such as
  `tkambio_5000`.
- `buy_price`: PEN needed to buy one USD.
- `sell_price`: PEN received for selling one USD.
- `timestamp`: a timezone-aware `datetime` from the source or the time of the fetch.

The `spread` property is `sell_price - buy_price`.
