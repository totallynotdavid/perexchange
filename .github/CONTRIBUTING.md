# Contributing to perexchange

For a substantial change, open an issue first so we can agree on the approach.

## The codebase

Read [architecture](../docs/architecture.md) first for the module map and fetch flow.

## Set up

Install [mise](https://mise.jdx.dev/). It provides the pinned `uv`, `ruff` and `bun`. Run
the commands below from the repository root.

```bash
git clone https://github.com/totallynotdavid/perexchange
cd perexchange
mise install
mise run sync
```

To try a change by hand, use the [CLI](../packages/cli/README.md) or run a script in
[`examples/`](../examples), such as `uv run python examples/basic.py`. Both send live
requests.

## Checks and tests

Run all checks:

```bash
mise run check
```

The task checks Python formatting and lint, Markdown and YAML formatting, types, unit
tests, and built packages. It never rewrites files.

Each part has its own task:

- `mise run test` runs the unit tests.
- `mise run format-check` checks Python formatting and lint with ruff.
- `mise run format-docs-check` checks Markdown and YAML formatting.
- `mise run lint` type-checks with mypy.
- `mise run build-check` builds the packages and verifies them.

Fix formatting with `mise run format` for Python and `mise run format-docs` for Markdown
and YAML.

Run one test file:

```bash
uv run pytest packages/core/tests/unit/test_parsers.py
```

Run the unit tests with a coverage report:

```bash
uv run pytest --cov=perexchange --cov-report=html
```

## Add a source

1. Add `packages/core/perexchange/scrapers/yoursite.py`. The module name is the source ID.
   Define `SOURCE` with that ID, and one parser, `_parse_json` or `_parse_html`, that
   turns the response into `ExchangeRate` objects carrying that ID. Build the fetcher with
   a factory from
   [`scrapers/factories.py`](../packages/core/perexchange/scrapers/factories.py) when the
   source fits one of its request patterns.
2. Add a `Source` for it to `_SOURCES` in
   [`scrapers/registry.py`](../packages/core/perexchange/scrapers/registry.py).
3. Save one representative response as `packages/core/tests/fixtures/yoursite.json` or
   `.html`.
4. Add the exact output to `EXPECTED_RATES` in
   [`test_parsers.py`](../packages/core/tests/unit/test_parsers.py).
5. Cover a parser branch that the representative response does not reach with a second
   fixture. Name it `yoursite-<case>`, add that name to `BRANCH_FIXTURES` in
   `test_parsers.py`, and write a test for it.

The parser suite fails when a registered source lacks a fixture or an `EXPECTED_RATES`
row, when a fixture belongs to no source, or when a parser accepts a malformed payload.
Put source-specific validation in the parser. The factory handles requests, retries, and
response decoding. Rules that span sources, such as dropping aggregator rows, belong in
`core.py` and its tests.

## Live tests

The live tests call the real exchange-house endpoints. They are not part of the default
tests, because endpoints can be slow, rate-limit requests, or change without notice. Run
them with:

```bash
mise run test-integration
```
