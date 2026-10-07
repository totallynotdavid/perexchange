# Architecture

perexchange has one public fetch layer and one adapter per external source. The fetch
layer decides which sources run, how long they get, and how their results combine. An
adapter turns one source's response into `ExchangeRate` values.

## Code map

Paths are relative to `packages/core/perexchange/`.

| Path                    | Responsibility                                                  |
| ----------------------- | --------------------------------------------------------------- |
| `__init__.py`           | The public API: `fetch_rates`, `fetch_rates_report`, the models |
| `core.py`               | The fetch flow below, and validation of the fetch settings      |
| `models.py`             | `ExchangeRate`, `SourceFailure` and `FetchReport`               |
| `errors.py`             | `ConfigurationError` and the expected source errors             |
| `retry.py`              | Retries with backoff, and conversion of parse errors            |
| `transport.py`          | The default `httpx.AsyncClient`, and `send()` for requests      |
| `time.py`               | Parsing of source timestamps                                    |
| `scrapers/registry.py`  | The catalog of sources and name resolution                      |
| `scrapers/factories.py` | Request patterns shared by adapters                             |
| `scrapers/base.py`      | The `ExchangeRateScraper` protocol every adapter satisfies      |
| `scrapers/<source>.py`  | One adapter: its URL and its parser                             |

Outside the package, `packages/core/tests/` holds the unit tests, the captured responses
in `fixtures/`, and the live tests in `integration/`. `packages/cli/` is the
[CLI](../packages/cli/README.md). `tools/build_check.py` verifies the built wheel and
source distribution.

## Fetch flow

`fetch_rates_report()` does the following:

1. Validate the settings and resolve the requested source names through the registry.
2. Create one `httpx.AsyncClient`, unless the caller supplies one.
3. Run the selected adapters concurrently.
4. Apply the request timeout, the retry policy, and the per-source total timeout.
5. Record expected failures in the report and let programming errors propagate.
6. Remove repeated `(source, name)` pairs, and aggregator rows for a house whose own
   source was selected and returned rates.

`fetch_rates()` calls `fetch_rates_report()` and returns only `report.rates`.

## Source registry

[`scrapers/registry.py`](../packages/core/perexchange/scrapers/registry.py) lists the
built-in sources. A `Source` holds its stable ID, its fetcher, its aliases, and whether it
is an aggregator.

The registry resolves IDs and aliases before any network request. It keeps the order of
the caller's selection and rejects unknown or repeated sources. Names compare after
lowercasing and removing accents and every character that is not a letter or digit.

## Adapter boundary

An adapter takes a shared client and the fetch settings and returns a list of
`ExchangeRate` objects. Every object carries the adapter's source ID. Both the factory and
the fetch layer check this.

Most adapters use a factory from
[`scrapers/factories.py`](../packages/core/perexchange/scrapers/factories.py):

- `json_scraper()` for one JSON request;
- `html_scraper()` for one HTML request;
- `dual_endpoint_json_scraper()` when buy and sell values use separate endpoints;
- `csrf_convert_scraper()` for a page-token and quote request;
- `digital_tc_scraper()` for the houses that share one platform API, selected by a tenant
  header.

The factory runs requests, decodes responses, and applies the retry policy. The adapter
maps fields and parses the source's format. `dichikash`, `okane` and `westernunion` call
`fetch_with_retry()` directly because their request flow fits no factory.

An adapter sends every request through `send()` in
[`transport.py`](../packages/core/perexchange/transport.py), never through the client's
methods.

A parser module defines one function, `_parse_json` or `_parse_html`. It returns every
valid row in the response. The fetch layer applies the rules that span sources.

## Failure boundary

`send()` turns any exception from the HTTP stack that is not an `httpx.HTTPError` into an
`httpx.TransportError`. A client the caller supplies can use a transport whose errors do
not derive from `httpx.HTTPError`, such as the protocol error of an HTTP/2 client, and
`send()` makes them retryable and reportable like any other transport error.

`fetch_with_retry()` retries transport errors and `408`, `429` and `5xx` responses. A
parse error stops the source at once and becomes a `SourceParseError`.

The fetch layer catches `httpx.HTTPError`, `SourceError` and timeouts for each source,
records them as `SourceFailure` values, and continues with the other sources. It does not
catch other exceptions.

One fetch call owns the default client and closes it on return. A client the caller passes
stays open, so a polling application can reuse its connections.
