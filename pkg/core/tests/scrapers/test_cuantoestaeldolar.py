from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from perexchange.scrapers.cuantoestaeldolar import (
    _parse_html,
    fetch_cuantoestaeldolar,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "cuantoestaeldolar"


def load_fixture(filename):
    with open(FIXTURES_DIR / filename, "r", encoding="utf-8") as f:
        return f.read()


def test_happy_path_extracts_valid_data():
    html = load_fixture("happy_path.html")
    rates = _parse_html(html)

    assert len(rates) >= 2

    for rate in rates:
        assert rate.name
        assert isinstance(rate.name, str)
        assert 2.0 <= rate.buy_price <= 5.0
        assert 2.0 <= rate.sell_price <= 5.0
        assert rate.sell_price > rate.buy_price
        assert 0 < rate.spread < 0.5
        assert rate.timestamp is not None


def test_known_houses_extracted():
    html = load_fixture("happy_path.html")
    rates = _parse_html(html)
    names = {r.name for r in rates}

    expected_houses = {"CambiaFX", "Câmbio & Compañía"}
    assert expected_houses.issubset(names)


def test_handles_special_characters_in_names():
    html = load_fixture("happy_path.html")
    rates = _parse_html(html)

    special_char_house = next(
        (r for r in rates if "Câmbio" in r.name or "&" in r.name),
        None,
    )
    assert special_char_house is not None


def test_skips_malformed_cards_gracefully():
    html = load_fixture("malformed_data.html")
    rates = _parse_html(html)

    assert len(rates) >= 1
    assert all(r.buy_price > 0 and r.sell_price > 0 for r in rates)


def test_tolerant_of_missing_optional_elements():
    html = load_fixture("missing_data.html")
    rates = _parse_html(html)
    assert len(rates) >= 2


def test_handles_css_class_hash_changes():
    html = load_fixture("changed_classes.html")
    rates = _parse_html(html)
    assert len(rates) >= 1


def test_fails_on_empty_html():
    html = load_fixture("empty.html")
    with pytest.raises(ValueError, match="No exchange houses found"):
        _parse_html(html)


@pytest.mark.asyncio
async def test_retries_on_network_errors():
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=[
                httpx.HTTPError("Connection failed"),
                httpx.HTTPError("Connection failed"),
                httpx.HTTPError("Connection failed"),
            ]
        )

        with pytest.raises(httpx.HTTPError):
            await fetch_cuantoestaeldolar(max_retries=3, retry_delay=0.01)

        assert mock_client.return_value.__aenter__.return_value.get.call_count == 3


@pytest.mark.asyncio
async def test_fails_fast_on_parsing_errors():
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.text = "<html><body>No exchange houses here</body></html>"
        mock_response.raise_for_status = Mock(return_value=None)

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="website structure may have changed"):
            await fetch_cuantoestaeldolar(max_retries=3, retry_delay=0.01)

        # Only one attempt - no retries for parsing errors
        assert mock_client.return_value.__aenter__.return_value.get.call_count == 1


@pytest.mark.asyncio
async def test_succeeds_after_transient_failure():
    html = load_fixture("happy_path.html")

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.text = html
        mock_response.raise_for_status = Mock(return_value=None)

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=[
                httpx.HTTPError("Temporary failure"),
                mock_response,
            ]
        )

        rates = await fetch_cuantoestaeldolar(max_retries=3, retry_delay=0.01)

        assert len(rates) >= 2
        assert mock_client.return_value.__aenter__.return_value.get.call_count == 2
