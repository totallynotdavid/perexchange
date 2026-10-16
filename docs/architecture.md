# Architecture

perexchange has one public fetch layer and one adapter per external source. The
fetch layer decides which sources run, how long they get, and how their results
combine. An adapter turns one source's response into `ExchangeRate` values.

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

Outside the package, `packages/core/tests/` holds the unit tests, the captured
responses in `fixtures/`, and the live tests in `integration/`. `packages/cli/`
is the [CLI](../packages/cli/README.md). `tools/build_check.py` verifies the
built wheel and source distribution.

## Fetch flow

`fetch_rates_report()` does the following:

1. Validate the settings and resolve the requested source names through the
   registry.
2. Create one `httpx.AsyncClient`, unless the caller supplies one.
3. Run the selected adapters concurrently.
4. Apply the request timeout, the retry policy, and the per-source total
   timeout.
5. Record expected failures in the report and let programming errors propagate.
6. Merge the results in selection order. The merge removes repeated
   `(source, name)` pairs and the aggregator rows that the
   [API reference](api.md#aggregators) describes.

`fetch_rates()` calls `fetch_rates_report()` and returns only `report.rates`.

## Source registry

[`scrapers/registry.py`](../packages/core/perexchange/scrapers/registry.py)
lists the built-in sources. A `Source` holds its stable ID, its fetcher, its
aliases, and whether it is an aggregator.

The registry resolves IDs and aliases before any network request. It keeps the
order of the caller's selection and rejects unknown or repeated sources. The
fetch layer also uses the registry to match an aggregator row to a house. The
[API reference](api.md#fetch-rates) describes how names match.

## Adapter boundary

An adapter takes a shared client and the fetch settings and returns a list of
`ExchangeRate` objects. Every object carries the adapter's source ID. The fetch
layer records a failure for an adapter whose rates carry another source ID.

Most adapters use a factory from
[`scrapers/factories.py`](../packages/core/perexchange/scrapers/factories.py):

- `json_scraper()` for one JSON request;
- `html_scraper()` for one HTML request;
- `dual_endpoint_json_scraper()` when buy and sell values use separate
  endpoints;
- `csrf_convert_scraper()` for a page-token and quote request;
- `digital_tc_scraper()` for the houses that share one platform API, selected by
  a tenant header.

The factory runs requests, decodes responses, and applies the retry policy. The
adapter maps fields and parses the source's format. `dichikash`, `okane` and
`westernunion` call `fetch_with_retry()` directly because their request flow
fits no factory.

An adapter sends every request through `send()` in
[`transport.py`](../packages/core/perexchange/transport.py), never through the
client's methods.

A parser module defines one function, `_parse_json` or `_parse_html`. It returns
every valid row in the response. The fetch layer applies the rules that span
sources.

## Failure boundary

`send()` turns any exception from the HTTP stack that is not an
`httpx.HTTPError` into an `httpx.TransportError`. A client the caller supplies
can use a transport whose errors do not derive from `httpx.HTTPError`, such as
the protocol error of an HTTP/2 client, and `send()` makes them retryable and
reportable like any other transport error.

`fetch_with_retry()` applies the [retry policy](api.md#retries). A parse error
stops the source at once and becomes a `SourceParseError`.

The fetch layer catches `httpx.HTTPError`, `SourceError` and timeouts for each
source, records them as `SourceFailure` values, and continues with the other
sources. It does not catch other exceptions.

One fetch call owns the default client and closes it on return. A client the
caller passes stays open, so a polling application can reuse its connections.

## Site data

The [site](../site/README.md) renders snapshots of `fetch_rates_report()`. The
only writer of the state below is the `snapshot` job of
[`.github/workflows/snapshot.yml`](../.github/workflows/snapshot.yml). A run of
it executes [`tools/collect.py`](../tools/collect.py) for 330 minutes. The
collector wakes every 15 minutes, fetches with
[`tools/snapshot.py`](../tools/snapshot.py) and pushes the result as one commit.
[Opening hours](#opening-hours) thin the fetches. Pull requests, the `check` job
and runs of other branches never write the data. The site reads the data branch
when a page renders.

GitHub's scheduler cannot keep a 15 minute beat. Asked for a run every 15
minutes, it started one about every five hours. So a run queues its own
successor, which starts when the run ends, and the schedule (hourly) and a
manual dispatch only restart a chain that broke.
[`tools/history_report.py`](../tools/history_report.py) prints the snapshots per
day and the median and maximum gap in minutes from the data branch.

### The state

| State                | Where                        | Holds                                                                                  |
| -------------------- | ---------------------------- | -------------------------------------------------------------------------------------- |
| The data branch      | the `data` branch, an orphan | `latest.json`, and `history/YYYY-MM-DD.jsonl` with one line per snapshot for a UTC day |
| The live site        | Vercel project `perexchange` | The docs pages, and a function that renders the rates pages from the data branch       |
| The publication lock | concurrency group `snapshot` | At most one running `snapshot` run, and at most one waiting                            |
| The job's worktree   | `site/data` on the runner    | A private checkout of the data branch. No other run reads or writes it                 |

### Transitions

The data branch is either absent or at a head commit, and only `snapshot` moves
it:

1. Absent to one commit. The first run creates the orphan branch, and the commit
   holds one snapshot.
2. Head to head plus one commit. The commit appends one line to the file for the
   UTC day of the fetch, which a new day creates, and replaces `latest.json`.
   The push is a fast-forward and never forced.

Nothing else is allowed. No run rewrites a history line, a commit, or the
branch. A run where no source returned a rate exits before the commit, so the
branch never gets an empty snapshot. A rejected push means the head moved, so
the run fails and the next run starts from the new head. A failed run holds the
lock for ten more minutes, so a fault that repeats does not restart every
minute.

A run takes these steps in order, and each depends on the one before:

1. Queue the next run.
2. Check out the head of the data branch.
3. Record a snapshot and push the commit, every 15 minutes, until 330 minutes
   have passed.

The lock lets one run hold these steps at a time. A running run is never
cancelled, because that could stop it between the record and the push. A newer
waiting run replaces an older waiting one. Every run does the same work, so the
one that takes over is whichever was queued last: the successor, a scheduled run
or a manual one. Only `master` records.

### Opening hours

The exchange houses close from 13:00 on Saturday, all day Sunday and on Peruvian
public holidays, all in Lima time (UTC-5, with no daylight saving time). The
holidays come from the PE calendar of the
[`holidays`](https://pypi.org/project/holidays/) package.
[`tools/hours.py`](../tools/hours.py) holds this rule and is its only copy.

At each wake the collector asks `tools/hours.py` whether to fetch:

- Outside the closed window the answer is always yes.
- Inside it the answer is yes only when the newest snapshot, the `generated_at`
  of `latest.json`, is 50 minutes old or older. With a 15 minute beat that is
  one fetch an hour. A snapshot that is missing or unreadable counts as due.

On no, the collector records nothing and waits for the next wake. The interval
stays below the three hours after which the site calls a snapshot
[old](../site/src/docs/data.md#how-fresh-it-is).

### What a reader sees

- A reader of the data branch sees the old commit or the new one, whole. One
  commit holds both files, and a ref update is atomic. A cached copy, such as a
  raw file URL, may lag by a short time.
- Vercel caches a rates page for 15 minutes
  ([`astro.config.mjs`](../site/astro.config.mjs)). The function keeps each file
  it read for 5 minutes ([`load.ts`](../site/src/lib/load.ts)), and GitHub
  caches a raw file for 5. A visitor sees data up to about 25 minutes older than
  the data branch. Two pages from different times can appear in one visit, one
  after the other.
- `/data/latest.json` tells clients to reuse it for 60 seconds
  ([`vercel.json`](../site/vercel.json)).
- The live site is never newer than the data branch. A run that fails leaves the
  branch where it was, and the pages keep showing it until the next run
  succeeds.
- The rules for old and unranked rates, and the warning on a stale snapshot, are
  in [Open data](../site/src/docs/data.md#how-fresh-it-is).
