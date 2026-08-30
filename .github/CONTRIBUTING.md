# Contributing

Run the commands below from the repository root.

## Set up

Install the workspace and development dependencies:

```bash
mise run sync
```

The CLI is optional. Run it from the workspace with:

```bash
uv run --package perexchange-cli perexchange help
```

## Checks and tests

Run the default checks with:

```bash
mise run check
```

This checks Python and documentation formatting, lint, types, unit tests, and package
artifacts. The formatting tasks rewrite files; the check tasks do not.

Run one part of the check when needed:

```bash
mise run test
mise run lint
mise run format
mise run format-docs
```

Run one test file with:

```bash
uv run pytest packages/core/tests/unit/test_parsers.py
```

Run coverage with:

```bash
uv run pytest --cov=perexchange --cov-report=html
```

## Add a scraper

The registry is the source of truth for accepted source names. Do not copy its list into
another module or document.

1. Add `packages/core/perexchange/scrapers/yoursite.py`. Define a stable `SOURCE` ID and
   parse the source response into `ExchangeRate` objects with that ID. Use a factory from
   [`scrapers/factories.py`](../packages/core/perexchange/scrapers/factories.py) when the
   source matches one of its request patterns.
2. Register the `Source` in `packages/core/perexchange/scrapers/registry.py`.
3. Save one representative response in `packages/core/tests/fixtures/yoursite.json` or
   `.html`.
4. Add the exact output to `EXPECTED_RATES` in `packages/core/tests/unit/test_parsers.py`.
5. Add a second fixture only for a parser branch that the representative response does not
   cover.

The parser suite requires one fixture and one expected-output row for every registered
source. It also rejects orphan fixtures. Keep source-specific validation in the parser;
the shared factory owns request, retry, and response-decoding behavior. Parser tests
should assert the source's complete response. Cross-source rules belong in core tests.

## Live integration tests

Integration tests call real exchange-house endpoints. They are separate from the default
test task because endpoints can be slow, rate-limit requests, or change outside this
repository.

Run them with:

```bash
mise run test-integration
```
