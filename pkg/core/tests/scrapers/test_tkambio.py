import json

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from perexchange.scrapers.tkambio import (
    _parse_json,
    fetch_tkambio,
)


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "tkambio"


def load_fixture(filename):
    with Path(FIXTURES_DIR / filename).open("r", encoding="utf-8") as f:
        return json.load(f)


def test_happy_path_extracts_valid_data():
    data = load_fixture("happy_path.json")
    rates = _parse_json(data)

    assert len(rates) == 3
    names = {r.name for r in rates}
    assert names == {"tkambio", "tkambio_5000", "tkambio_10000"}

    for rate in rates:
        assert rate.name
        assert 2.0 <= rate.buy_price <= 5.0
        assert 2.0 <= rate.sell_price <= 5.0
        assert rate.sell_price > rate.buy_price
        assert 0 < rate.spread < 0.5
        assert rate.timestamp is not None


def test_skips_malformed_data_gracefully():
    data = load_fixture("malformed_data.json")
    rates = _parse_json(data)

    # Should skip invalid base rate but accept discounts even with non-int min_amount
    assert len(rates) == 2
    names = {r.name for r in rates}
    assert "tkambio_10000" in names


def test_tolerant_of_missing_keys():
    data = load_fixture("missing_data.json")
    rates = _parse_json(data)

    # Missing buying_rate in base, but valid discount
    assert len(rates) == 1
    assert rates[0].name == "tkambio_5000"


def test_handles_empty_response():
    data = load_fixture("empty.json")
    with pytest.raises(ValueError, match="No valid exchange rates parsed"):
        _parse_json(data)


@pytest.mark.asyncio
async def test_retries_on_network_errors():
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=[
                httpx.HTTPError("Connection failed"),
                httpx.HTTPError("Connection failed"),
                httpx.HTTPError("Connection failed"),
            ]
        )

        with pytest.raises(httpx.HTTPError):
            await fetch_tkambio(max_retries=3, retry_delay=0.01)

        assert mock_client.return_value.__aenter__.return_value.post.call_count == 3


@pytest.mark.asyncio
async def test_fails_fast_on_parsing_errors():
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value={"invalid": "data"})
        mock_response.raise_for_status = Mock(return_value=None)

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        with pytest.raises(ValueError, match="API structure may have changed"):
            await fetch_tkambio(max_retries=3, retry_delay=0.01)

        # Only one attempt
        assert mock_client.return_value.__aenter__.return_value.post.call_count == 1


@pytest.mark.asyncio
async def test_succeeds_after_transient_failure():
    data = load_fixture("happy_path.json")

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value=data)
        mock_response.raise_for_status = Mock(return_value=None)

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=[
                httpx.HTTPError("Temporary failure"),
                mock_response,
            ]
        )

        rates = await fetch_tkambio(max_retries=3, retry_delay=0.01)

        assert len(rates) == 3
        assert mock_client.return_value.__aenter__.return_value.post.call_count == 2
