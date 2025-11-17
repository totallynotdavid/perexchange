# For devs

Install core package in editable mode:

```bash
cd pkg/core
pip install -e ".[dev]"
```

Install CLI (optional):

```bash
cd pkg/cli
pip install -e .
```

Run unit tests:

```bash
pytest
```

Run integration tests (hits real websites).

```bash
pytest -m integration
```

Run specific test files:

```bash
pytest tests/scrapers/test_somescraper.py
```

Run with coverage:

```bash
pytest --cov=perexchange --cov-report=html
```

The project uses ruff and mypy for linting, formatting and type checking. You can test
things with:

```bash
ruff check .
ruff format .
mypy perexchange tests
```

## Adding new scrapers

1. Create the scraper file in: `perexchange/scrapers/yoursite.py`
2. Implement an async function returning a list of ExchangeRate objects.
3. Register it in: `perexchange/scrapers/__init__.py`
4. Add tests in: `tests/scrapers/test_yoursite.py`
5. Add fixtures in: `tests/scrapers/fixtures/yoursite/`

Example scraper outline:

```python
async def fetch_yoursite(url: str, timeout: float, max_retries: int):
    return rates
```

## Integration tests

Integration tests fetch real websites and exist to detect layout or data changes. They run
periodically on CI.

Example:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_real_website():
    rates = await fetch_rates()
    assert len(rates) > 0
```

---

The project has mise set up, you can simplify the commands using:

```bash
mise run test
mise run lint
mise run build
```
