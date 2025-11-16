from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from perexchange.core import fetch_rates

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename):
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.mark.asyncio
async def test_happy_path():
    html = load_fixture("happy_path.html")

    mock_response = AsyncMock()
    mock_response.text = html
    mock_response.raise_for_status = Mock(return_value=None)

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        rates = await fetch_rates()
        assert len(rates) == 2
        assert rates[0].name == "CambiaFX"
        assert rates[0].buy_price == 3.352
        assert rates[0].sell_price == 3.378
        assert rates[1].name == "Câmbio & Compañía"


@pytest.mark.asyncio
async def test_malformed_data_skips_invalid():
    html = load_fixture("malformed_data.html")

    mock_response = AsyncMock()
    mock_response.text = html
    mock_response.raise_for_status = Mock(return_value=None)

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        rates = await fetch_rates()
        assert len(rates) == 1
        assert rates[0].name == "Okane"


@pytest.mark.asyncio
async def test_missing_data_still_parses():
    html = load_fixture("missing_data.html")

    mock_response = AsyncMock()
    mock_response.text = html
    mock_response.raise_for_status = Mock(return_value=None)

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        rates = await fetch_rates()
        assert len(rates) == 2
        assert rates[0].name == "Inka Money"
        assert rates[1].name == "Rextie"


@pytest.mark.asyncio
async def test_empty_html():
    html = load_fixture("empty.html")

    mock_response = AsyncMock()
    mock_response.text = html
    mock_response.raise_for_status = Mock(return_value=None)

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="No exchange houses found"):
            await fetch_rates()


@pytest.mark.asyncio
async def test_retry_on_http_error():
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=[
                httpx.HTTPError("Connection failed"),
                httpx.HTTPError("Connection failed"),
                httpx.HTTPError("Connection failed"),
            ]
        )

        with pytest.raises(httpx.HTTPError):
            await fetch_rates(max_retries=3, retry_delay=0.01)

        assert mock_client.return_value.__aenter__.return_value.get.call_count == 3


@pytest.mark.asyncio
async def test_timeout_configuration():
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = Mock(return_value=None)

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        try:
            await fetch_rates(timeout=5.0)
        except ValueError:
            pass

        mock_client.assert_called_with(timeout=5.0)
