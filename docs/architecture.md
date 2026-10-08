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

## Site data

The [site](../site/README.md) is static pages built from snapshots of
`fetch_rates_report()`. The only writer of the state below is the `publish` job of
[`.github/workflows/site.yml`](../.github/workflows/site.yml), which runs every 15 minutes
and on each push to `master`. Pull requests, the `check` job and manual runs of other
branches never write it.

### The state

| State                | Where                          | Holds                                                                                  |
| -------------------- | ------------------------------ | -------------------------------------------------------------------------------------- |
| The data branch      | the `data` branch, an orphan   | `latest.json`, and `history/YYYY-MM-DD.jsonl` with one line per snapshot for a UTC day |
| The live site        | Cloudflare Workers assets      | One build: its pages and `/data/latest.json`                                           |
| The publication lock | concurrency group `site-<ref>` | At most one running `publish` run, and at most one waiting                             |
| The job's worktree   | `site/data` on the runner      | A private checkout of the data branch. No other run reads or writes it                 |

The build cache of `setup-uv` is keyed by the lockfile. A miss costs time and nothing
else.

### Transitions

The data branch is either absent or at a head commit, and only `publish` moves it:

1. Absent to one commit. The first run creates the orphan branch, and the commit holds one
   snapshot.
2. Head to head plus one commit. The commit appends one line to the file for the UTC day
   of the fetch, which a new day creates, and replaces `latest.json`. The push is a
   fast-forward and never forced.

Nothing else is allowed. No run rewrites a history line, a commit, or the branch. A run
where no source returned a rate exits before the commit, so the branch never gets an empty
snapshot. A rejected push means the head moved, so the run fails and the next run starts
from the new head.

A run takes these steps in order, and each depends on the one before:

1. Check that its commit is the head of `master`. A re-run of an old run fails here
   instead of deploying old code.
2. Check out the head of the data branch.
3. Record a snapshot, then push the commit.
4. Build from that worktree.
5. Deploy the build. A run without the Cloudflare token stops here and warns.

The lock lets one run hold steps 1 to 5 at a time. A running run is never cancelled,
because that could stop it between the push and the deploy. A newer waiting run replaces
an older waiting one, so a busy period costs snapshots, not consistency. Only `master`
publishes, whether the run was scheduled, pushed or started by hand.

### What a reader sees

- A reader of the data branch sees the old commit or the new one, whole. One commit holds
  both files, and a ref update is atomic. A cached copy, such as a raw file URL, may lag
  by a short time.
- A visitor sees one build. Every page of a build and its `/data/latest.json` come from
  the same snapshot, and Cloudflare switches to a new build as a whole. Pages from two
  builds can appear in one visit, one after the other.
- The live site is never newer than the data branch, because a run pushes before it
  builds. It can be older when a deploy fails or no token is set. The next run that
  deploys rebuilds from the whole branch and catches up.
- The page shows the time of its snapshot and warns when it is more than an hour old, so a
  stopped schedule is visible.
