import asyncio

import httpx
import pytest

from bs4 import BeautifulSoup


async def retry_request(method, url, max_attempts=3, **kwargs):
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if method == "GET":
                    response = await client.get(url, **kwargs)
                else:
                    response = await client.post(url, **kwargs)
                response.raise_for_status()
                return response
        except Exception as e:  # noqa: BLE001 (intentional for retry on any error from flaky APIs)
            if attempt == max_attempts - 1:
                pytest.fail(f"Request failed after {max_attempts} attempts: {e}")
            await asyncio.sleep(1)
    return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cambioseguro_api_schema():
    url = "https://api.cambioseguro.com/api/v1.1/config/rates"
    response = await retry_request("GET", url)
    data = response.json()

    assert "data" in data, "Missing 'data' key in response"

    required_fields = [
        "purchase_price",
        "sale_price",
        "purchase_price_comparative",
        "sale_price_comparative",
        "purchase_price_paralelo",
        "sale_price_paralelo",
    ]

    for field in required_fields:
        assert field in data["data"], f"Missing required field: {field}"
        value = data["data"][field]
        assert isinstance(value, (int, float)), (
            f"{field} should be numeric, got {type(value)}"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cuantoestaeldolar_html_schema():
    url = "https://cuantoestaeldolar.pe/cambio-de-dolar-online"
    response = await retry_request("GET", url)
    soup = BeautifulSoup(response.text, "lxml")

    buttons = soup.find_all("a", string="CAMBIAR")
    assert len(buttons) >= 5, "Expected at least 5 exchange houses"

    for button in buttons[:3]:
        parent = button.find_parent("div")
        assert parent, "Button should have parent div"

        card = parent.find_parent("div")
        assert card, "Should have card container"

        img = card.find("img")
        assert img, "Card should have image"
        assert img.get("alt"), "Image should have alt text"

        buy_block = card.select_one('div[class*="_content_buy__"]')
        sell_block = card.select_one('div[class*="_content_sale__"]')
        assert buy_block, "Card should have buy block"
        assert sell_block, "Card should have sell block"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tkambio_api_schema():
    url = "https://tkambio.com/wp-admin/admin-ajax.php"
    response = await retry_request(
        "POST",
        url,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        },
        data={"action": "get_exchange_rate"},
    )
    data = response.json()

    assert "buying_rate" in data, "Missing 'buying_rate' key"
    assert "selling_rate" in data, "Missing 'selling_rate' key"
    assert isinstance(data["buying_rate"], (int, float))
    assert isinstance(data["selling_rate"], (int, float))

    if "discounts" in data:
        assert isinstance(data["discounts"], list)
        for discount in data["discounts"]:
            assert "min_amount" in discount
            assert "buying_rate" in discount
            assert "selling_rate" in discount


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tucambista_api_schema():
    url = "https://apim.tucambista.pe/api/rates"
    response = await retry_request(
        "GET",
        url,
        headers={
            "ocp-apim-subscription-key": "e4b6947d96a940e7bb8b39f462bcc56d;product=tucambista-production",
        },
    )
    data = response.json()

    assert "bidRate" in data, "Missing 'bidRate' key"
    assert "offerRate" in data, "Missing 'offerRate' key"
    assert isinstance(data["bidRate"], (int, float))
    assert isinstance(data["offerRate"], (int, float))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_westernunion_has_verification_token():
    page_url = "https://www.westernunionperu.pe/cambiodemoneda"
    response = await retry_request("GET", page_url)
    soup = BeautifulSoup(response.text, "html.parser")

    token_input = soup.find("input", {"name": "__RequestVerificationToken"})
    assert token_input, "Missing CSRF token input"

    token = token_input.get("value")
    assert token, "CSRF token is empty"
    assert isinstance(token, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_westernunion_api_schema():
    page_url = "https://www.westernunionperu.pe/cambiodemoneda"
    api_url = "https://www.westernunionperu.pe/cambiodemoneda/Operation/PostTipoCambio"

    page_response = await retry_request("GET", page_url)
    soup = BeautifulSoup(page_response.text, "html.parser")
    token_input = soup.find("input", {"name": "__RequestVerificationToken"})
    token = token_input.get("value")

    api_response = await retry_request(
        "POST",
        api_url,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": page_url,
        },
        data={
            "monto": "1000",
            "moneda": "2",
            "tipo": "1",
            "__RequestVerificationToken": token,
            "ERequestServicesGeneral[Recaptcha]": "",
        },
    )
    data = api_response.json()

    assert "DT_Compra" in data, "Missing 'DT_Compra' key"
    assert "DT_Venta" in data, "Missing 'DT_Venta' key"
    assert isinstance(data["DT_Compra"], (int, float))
    assert isinstance(data["DT_Venta"], (int, float))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_instakash_html_schema():
    url = "https://instakash.net/"
    response = await retry_request("GET", url)
    soup = BeautifulSoup(response.text, "html.parser")

    rates_container = soup.find(
        "div", class_="flex items-center justify-center text-primary gap-10 py-1"
    )
    assert rates_container, "Missing rates container"

    rate_items = rates_container.find_all("div", recursive=False)
    assert len(rate_items) >= 3, "Expected at least 3 rate items"

    compra_div = rate_items[0]
    venta_div = rate_items[2]

    compra_p = compra_div.find("p", class_="font-semibold")
    venta_p = venta_div.find("p", class_="font-semibold")

    assert compra_p, "Missing compra rate element"
    assert venta_p, "Missing venta rate element"
    assert compra_p.get_text(strip=True), "Compra rate is empty"
    assert venta_p.get_text(strip=True), "Venta rate is empty"
