# How perexchange works

`perexchange` is a set of adapters with one public fetch function. Each adapter turns one
exchange-house response into zero or more `ExchangeRate` objects.

## Fetch path

`fetch_rates()` follows this path:

1. The [registry](../packages/core/perexchange/scrapers/registry.py) resolves the
   requested house names to scrapers.
2. One `httpx.AsyncClient` is shared by the selected scrapers.
3. The scrapers run concurrently and parse their own response formats.
4. Expected transport and parsing failures are isolated to the scraper that raised them.
5. Results are flattened in selected-house order. Duplicate rate names keep the first
   result.

The public behavior of `fetch_rates()` is documented in the
[API reference](../packages/core/readme.md).

## Scraper boundary

A scraper accepts the shared client and the fetch settings, then returns a list of
`ExchangeRate` objects. Most scrapers use a factory from
[`scrapers/base.py`](../packages/core/perexchange/scrapers/base.py):

- `json_scraper()` for one JSON request;
- `html_scraper()` for one HTML request;
- `dual_endpoint_json_scraper()` when buy and sell values come from separate endpoints;
- `csrf_convert_scraper()` for the shared page-token-and-quote flow.

The factory owns request execution, response decoding, and retries. The adapter owns the
source-specific field mapping and validation. Keep external response quirks beside the
parser that handles them.

The aggregator adapter calls the registry's name matcher when filtering display names. It
does not keep a second house list, so a quote covered by a dedicated adapter is not
returned again.

## Failure boundary

[`fetch_with_retry()`](../packages/core/perexchange/scrapers/base.py) retries transport
errors and temporary HTTP responses. Parser errors stop that scraper immediately. The
outer fetch path logs expected failures and keeps successful results from other scrapers.
The registry rejects unknown house names before any request starts.
