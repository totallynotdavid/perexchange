# Contributing

Run these commands from the repository root. Install the workspace and development
dependencies with:

```bash
mise run sync
```

The CLI is optional. Run it through the workspace with:

```bash
uv run --package perexchange-cli perexchange help
```

The fetch path is described in [the architecture notes](../docs/architecture.md).

## Development commands

```bash
mise run check
```

Run individual commands when debugging:

```bash
mise run test
mise run lint
mise run format
mise run format-docs
```

`format` and `format-docs` rewrite files. `mise run check` only verifies them.

Integration tests hit real websites and are intentionally separate:

```bash
mise run test-integration
```

Run a specific test file with:

```bash
uv run pytest packages/core/tests/unit/test_parsers.py
```

Run coverage with:

```bash
uv run pytest --cov=perexchange --cov-report=html
```

## Adding new scrapers

The registry is the source of truth for available houses. Do not copy its list into
another module or document.

1. Create `packages/core/perexchange/scrapers/yoursite.py`. Parse the raw response into
   `ExchangeRate` objects and use a factory from `scrapers/base.py` when the request fits
   one of the shared protocols.
2. Import and register the fetcher in `packages/core/perexchange/scrapers/registry.py`.
3. Save one representative response as `packages/core/tests/fixtures/yoursite.json` or
   `.html`.
4. Add the exact parsed output to `EXPECTED_RATES` in
   `packages/core/tests/unit/test_parsers.py`.
5. Add a separate branch fixture only when the parser must protect a behavior that the
   representative response does not cover.

The parser tests require one representative fixture and one expected-output row for each
registered house. They also reject orphan fixtures. The integration suite covers live
requests separately.

Example scraper:

```python
from datetime import datetime, timezone
from typing import Any

from perexchange.models import ExchangeRate
from perexchange.scrapers.base import json_scraper, rate_from_fields


URL = "https://yoursite.pe/api/rates"


def _parse_json(data: dict[str, Any]) -> list[ExchangeRate]:
    rate = rate_from_fields(
        data, "yoursite", "compra", "venta", datetime.now(timezone.utc)
    )
    if rate is None:
        msg = "No valid exchange rates parsed"
        raise ValueError(msg)
    return [rate]


fetch_yoursite = json_scraper(URL, _parse_json)
```

Keep validation that protects a business mapping in the parser. Let the shared scraper
factory own transport, retry, and response-decoding behavior.

## Integration tests

Integration tests fetch real websites to detect layout and data changes. They run
periodically on CI.

The integration suite is separate because exchange-house endpoints can rate-limit or block
repeated requests.
