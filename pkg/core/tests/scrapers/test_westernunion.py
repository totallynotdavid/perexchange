import json

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from perexchange.scrapers.westernunion import (
    _parse_json,
    fetch_westernunion,
)


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "westernunion"


def load_json_fixture(filename):
    with Path(FIXTURES_DIR / filename).open("r", encoding="utf-8") as f:
        return json.load(f)


def load_html_fixture(filename):
    with Path(FIXTURES_DIR / filename).open("r", encoding="utf-8") as f:
        return f.read()


def test_happy_path_extracts_valid_data():
    data = load_json_fixture("happy_path.json")
    rates = _parse_json(data)

    assert len(rates) == 1
    rate = rates[0]
    assert rate.name == "westernunion"
    assert rate.buy_price == 3.352
    assert rate.sell_price == 3.374
    assert rate.sell_price > rate.buy_price
    assert 0 < rate.spread < 0.1
    assert rate.timestamp is not None


def test_skips_malformed_data_gracefully():
    data = load_json_fixture("malformed_data.json")
    with pytest.raises(ValueError, match="No valid exchange rates parsed"):
        _parse_json(data)


def test_tolerant_of_missing_keys():
    data = load_json_fixture("missing_data.json")
    with pytest.raises(ValueError, match="No valid exchange rates parsed"):
        _parse_json(data)


def test_handles_empty_response():
    data = {}
    with pytest.raises(ValueError, match="No valid exchange rates parsed"):
        _parse_json(data)


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
            await fetch_westernunion(max_retries=3, retry_delay=0.01)

        assert mock_client.return_value.__aenter__.return_value.get.call_count == 3


@pytest.mark.asyncio
async def test_fails_fast_on_parsing_errors():
    html = load_html_fixture("page.html")
    data = {"invalid": "data"}

    with patch("httpx.AsyncClient") as mock_client:
        mock_page_response = AsyncMock()
        mock_page_response.text = html
        mock_page_response.raise_for_status = Mock(return_value=None)

        mock_api_response = AsyncMock()
        mock_api_response.json = Mock(return_value=data)
        mock_api_response.raise_for_status = Mock(return_value=None)

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_page_response
        )
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_api_response
        )

        with pytest.raises(ValueError, match="API structure may have changed"):
            await fetch_westernunion(max_retries=3, retry_delay=0.01)

        # Only one attempt
        assert mock_client.return_value.__aenter__.return_value.post.call_count == 1


@pytest.mark.asyncio
async def test_succeeds_after_transient_failure():
    html = load_html_fixture("page.html")
    data = load_json_fixture("happy_path.json")

    with patch("httpx.AsyncClient") as mock_client:
        mock_page_response = AsyncMock()
        mock_page_response.text = html
        mock_page_response.raise_for_status = Mock(return_value=None)

        mock_api_response = AsyncMock()
        mock_api_response.json = Mock(return_value=data)
        mock_api_response.raise_for_status = Mock(return_value=None)

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=[
                httpx.HTTPError("Temporary failure"),
                mock_page_response,
            ]
        )
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_api_response
        )

        rates = await fetch_westernunion(max_retries=3, retry_delay=0.01)

        assert len(rates) == 1
        assert mock_client.return_value.__aenter__.return_value.get.call_count == 2
        assert mock_client.return_value.__aenter__.return_value.post.call_count == 1


@pytest.mark.asyncio
async def test_fails_on_missing_token():
    html = "<html><body>No token here</body></html>"

    with patch("httpx.AsyncClient") as mock_client:
        mock_page_response = AsyncMock()
        mock_page_response.text = html
        mock_page_response.raise_for_status = Mock(return_value=None)

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_page_response
        )

        with pytest.raises(ValueError, match="Failed to parse exchange rates"):
            await fetch_westernunion(max_retries=3, retry_delay=0.01)

        # Should not attempt API call
        assert mock_client.return_value.__aenter__.return_value.post.call_count == 0
