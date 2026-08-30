# Architecture

`perexchange` turns several exchange-house responses into one list of `ExchangeRate`
objects. The public result contract is documented in the
[core API reference](../packages/core/readme.md).

1. [`fetch_rates()`](../packages/core/perexchange/core.py) asks the
   [registry](../packages/core/perexchange/scrapers/registry.py) for the selected
   scrapers.
2. One shared `httpx.AsyncClient` is passed to every scraper.
3. Scrapers run through `asyncio.gather()` and translate source-specific responses into
   `ExchangeRate` objects.
4. Expected transport and parsing failures are isolated per scraper.
5. Duplicate rate names keep the first result in selected-house order.

The registry is the source of truth for accepted house names. The aggregator scraper uses
the registry's name matching rather than maintaining a second list of houses. Its
dedicated tests are in [test_parsers.py](../packages/core/tests/unit/test_parsers.py).

## Adapter boundary

- A house is a key in the registry and an input accepted by `fetch_rates()`.
- A scraper is the callable that fetches and parses one house.
- A rate name identifies one returned quote. A scraper can emit multiple rate names for
  tiers or variants.

Most one-endpoint scrapers use the shared factories in
[base.py](../packages/core/perexchange/scrapers/base.py). Scrapers with multiple requests
keep those requests inside one retry operation. Source-specific mapping rules stay beside
the parser that owns them.

## Failure boundary

[`fetch_with_retry()`](../packages/core/perexchange/scrapers/base.py) retries transport
failures and temporary HTTP responses, but stops immediately for parser failures. The
outer fetch path logs expected failures and keeps successful results from other houses.
Invalid house names are validated by the registry before any request starts.
