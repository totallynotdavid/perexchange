# Architecture

`perexchange` has one public fetch layer and one adapter per external source.

## Fetch flow

`fetch_rates_report()` does the following:

1. Resolve the requested source names through the registry.
2. Create one `httpx.AsyncClient`, unless the caller supplies one.
3. Run the selected source adapters concurrently.
4. Apply the request timeout, retry policy, and per-source total timeout.
5. Keep expected failures in the report and let programming errors propagate.
6. Remove duplicate `(source, name)` pairs and aggregator rows covered by a dedicated
   adapter.

`fetch_rates()` is the convenience form. It returns only `report.rates`. Callers that need
to explain missing data should use `fetch_rates_report()`.

## Source registry

[`scrapers/registry.py`](../packages/core/perexchange/scrapers/registry.py) is the source
of truth for built-in adapters. A `Source` contains its stable ID, fetcher, aliases, and
whether it is an aggregator.

The registry resolves IDs and aliases before any network request. It preserves the order
of the caller's selection and rejects unknown or repeated sources.

The registry is deliberately a fixed catalog. Adding a source means adding code and tests;
there is no plugin discovery step to hide import errors or make release behavior depend on
the environment.

## Adapter boundary

An adapter accepts a shared client and fetch settings and returns a list of `ExchangeRate`
objects. Every returned object carries the adapter's stable source ID. The factory and
public fetch layer both enforce that invariant.

Most adapters use a factory from
[`scrapers/factories.py`](../packages/core/perexchange/scrapers/factories.py):

- `json_scraper()` for one JSON request;
- `html_scraper()` for one HTML request;
- `dual_endpoint_json_scraper()` when buy and sell values use separate endpoints;
- `csrf_convert_scraper()` for a page-token and quote request.

The factory owns request execution, response decoding, and retries. The adapter owns field
mapping and source-specific parsing. Custom adapters use the same retry helper directly
when their request flow cannot use a factory.

Parser functions return every valid row in the source response. The core layer owns
cross-source rules such as aggregator filtering and duplicate handling, so those rules do
not drift between adapters.

## Failure boundary

The retry helper retries transport errors and temporary HTTP responses. Parse errors stop
the current source immediately because repeating the same response will not repair its
shape.

The fetch layer catches expected HTTP, timeout, and source errors for each source. It
records them as `SourceFailure` values and continues with the other sources. It does not
catch arbitrary exceptions: a programming error should fail loudly and be fixed.

The default transport client is owned by one fetch call and closed when that call returns.
A caller-owned client stays open so polling applications can reuse its connections.
