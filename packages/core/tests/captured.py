"""A client that answers every source from the captured responses in `fixtures/`."""

from importlib import import_module
from pathlib import Path

import httpx

from perexchange.scrapers.factories import DIGITAL_TC_URL
from perexchange.scrapers.registry import get_sources


FIXTURES = Path(__file__).parent / "fixtures"
DIGITAL_TENANTS = {"sr-cambio": "srcambio", "money-plus": "moneyplus"}


def fixture_bytes(stem: str) -> bytes:
    [path] = FIXTURES.glob(f"{stem}.*")
    return path.read_bytes()


def fixture_client() -> httpx.AsyncClient:
    """Answer each source that has a single `URL` with its fixture, and the rest `404`."""
    bodies: dict[str, bytes] = {}
    for source in get_sources():
        url = getattr(import_module(f"perexchange.scrapers.{source.id}"), "URL", None)
        if url is not None:
            bodies[str(httpx.URL(url))] = fixture_bytes(source.id)

    def answer(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == DIGITAL_TC_URL:
            tenant = DIGITAL_TENANTS[request.headers["X-Digital-Tenant"]]
            return httpx.Response(200, content=fixture_bytes(tenant))
        if url in bodies:
            return httpx.Response(200, content=bodies[url])
        return httpx.Response(404)

    return httpx.AsyncClient(transport=httpx.MockTransport(answer))
