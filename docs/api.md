# API reference

`perexchange` exports `fetch_rates()`, `fetch_rates_report()`, the data classes
`ExchangeRate`, `FetchReport` and `SourceFailure`, the exception `ConfigurationError`, and
`__version__`.

## Fetch rates

```python
import asyncio

import perexchange


async def main() -> None:
    rates = await perexchange.fetch_rates(sources=["cambiafx", "tucambista"])
    for rate in rates:
        print(rate.source, rate.name, rate.buy_price, rate.sell_price)


asyncio.run(main())
```

With no `sources` argument, `fetch_rates()` queries every registered source. Source names
are matched without regard to case, accents, spaces, or punctuation. `kambioonline2` is an
alias for `kambioonline`.

Results keep the order of `sources`. A repeated `(source, name)` pair keeps its first
value.

### Aggregators

`cuantoestaeldolar` is an aggregator. It lists many houses, and some of them also have a
source of their own. Select it alone and you get a rate for every house it lists. Select
it together with a house's own source, and its row for that house is dropped when the
house's source returned rates. If the house's own source failed, the aggregator's row
stays.

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

- `timeout` limits each HTTP request, in seconds.
- `max_attempts` is the total number of attempts for each source, including the first.
- `total_timeout` limits one source's whole operation, including retries and backoff. Set
  it to `None` to remove the limit.
- `client` is a shared `httpx.AsyncClient`. If you pass one, `perexchange` leaves it open.
  Otherwise it creates a client that can use HTTP/2 and closes it before returning.

`fetch_rates_report()` takes the same arguments.

### Retries

A source is retried after a transport error or a `408`, `429` or `5xx` response. Other
`4xx` responses and parse errors are not retried. The wait before the next attempt is 0.5
seconds, doubling after each attempt.

For a `429` response, a numeric `Retry-After` header sets the wait, up to 30 seconds. A
`429` without a numeric `Retry-After` waits at least 5 seconds.

Some sources need more than one request. A retry repeats all of that source's requests.

## Failures

`fetch_rates()` leaves out a source that fails. `fetch_rates_report()` returns a
`FetchReport` with the rates and the failures, so you can tell an empty result from a
failed one:

```python
report = await perexchange.fetch_rates_report()

for failure in report.failures:
    print(f"{failure.source}: {failure.error_type}: {failure.message}")
```

`report.rates` is a tuple of `ExchangeRate`. `report.failures` is a tuple of
`SourceFailure`, each with `source`, `error_type` and `message`. Each failure is also
logged at `WARNING` on the `perexchange` logger.

A transport failure, a timeout and an unparseable response are recorded as failures and
never fail the whole call. Any exception raised while a request is sent counts as a
transport failure, even one that is not an `httpx` error, such as the protocol error of a
custom HTTP/2 transport. It is recorded with the error type `TransportError`. An exception
raised anywhere else propagates, so a programming error is not hidden.

### `ConfigurationError`

`ConfigurationError` is a `ValueError`. It is raised before any request starts when:

- a source is unknown or selected twice;
- `sources` is a string instead of a sequence of names;
- `timeout` or `total_timeout` is not a positive finite number;
- `max_attempts` is not an integer of at least 1.

## `ExchangeRate`

`ExchangeRate` is an immutable dataclass with these fields:

- `source`: the stable source ID, such as `cambiafx`.
- `name`: the quote's label. For a source with one quote it equals `source`. Otherwise it
  names the variant or tier, such as `tkambio_5000` or `cambioseguro_paralelo`. For the
  aggregator it is the house's name.
- `buy_price`: PEN the house pays for one USD. This is what you receive when you sell a
  dollar.
- `sell_price`: PEN the house charges for one USD. This is what you pay when you buy a
  dollar.
- `timestamp`: a timezone-aware `datetime`, from the source when it provides one and from
  the time of the fetch otherwise.

The `spread` property is `sell_price - buy_price`.

To find where to buy a dollar cheapest, take the lowest `sell_price`. To find where to
sell one for the most, take the highest `buy_price`.
[`examples/best_rates.py`](../examples/best_rates.py) does both.
