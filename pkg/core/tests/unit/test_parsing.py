import json

from pathlib import Path

import pytest

from perexchange.scrapers.cambiafx import _parse_json as parse_cambiafx
from perexchange.scrapers.cambioseguro import _parse_json as parse_cambioseguro
from perexchange.scrapers.cuantoestaeldolar import (
    _parse_html as parse_cuantoestaeldolar,
)
from perexchange.scrapers.instakash import _parse_html as parse_instakash
from perexchange.scrapers.srcambio import _parse_json as parse_srcambio
from perexchange.scrapers.tkambio import _parse_json as parse_tkambio
from perexchange.scrapers.tucambista import _parse_json as parse_tucambista
from perexchange.scrapers.westernunion import _parse_json as parse_westernunion


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_json(house, filename):
    path = FIXTURES_DIR / house / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_html(house, filename):
    path = FIXTURES_DIR / house / filename
    with path.open("r", encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "fixture,expected_count,should_fail",
    [
        ("happy_path.json", 3, False),
        ("malformed_data.json", 1, False),
        ("missing_data.json", 0, True),
        ("empty.json", 0, True),
    ],
)
def test_cambioseguro_parsing(fixture, expected_count, should_fail):
    data = load_json("cambioseguro", fixture)

    if should_fail:
        with pytest.raises(ValueError, match="No valid exchange rates"):
            parse_cambioseguro(data)
    else:
        rates = parse_cambioseguro(data)
        assert len(rates) == expected_count
        for rate in rates:
            assert 2.0 <= rate.buy_price <= 5.0
            assert 2.0 <= rate.sell_price <= 5.0
            assert rate.spread > 0


@pytest.mark.parametrize(
    "fixture,expected_count,should_fail",
    [
        ("happy_path.json", 1, False),
        ("malformed_data.json", 0, True),
        ("missing_data.json", 0, True),
        ("empty.json", 0, True),
    ],
)
def test_cambiafx_parsing(fixture, expected_count, should_fail):
    data = load_json("cambiafx", fixture)

    if should_fail:
        with pytest.raises(
            ValueError, match=r"No valid exchange rates|No exchange rates data"
        ):
            parse_cambiafx(data)
    else:
        rates = parse_cambiafx(data)
        assert len(rates) == expected_count
        for rate in rates:
            assert 2.0 <= rate.buy_price <= 5.0
            assert 2.0 <= rate.sell_price <= 5.0
            assert rate.spread > 0


@pytest.mark.parametrize(
    "fixture,expected_count,should_fail",
    [
        ("happy_path.html", 2, False),
        ("changed_classes.html", 1, False),
        ("malformed_data.html", 1, False),
        ("missing_data.html", 2, False),
        ("empty.html", 0, True),
    ],
)
def test_cuantoestaeldolar_parsing(fixture, expected_count, should_fail):
    html = load_html("cuantoestaeldolar", fixture)

    if should_fail:
        with pytest.raises(ValueError, match=r"No exchange houses found|No valid"):
            parse_cuantoestaeldolar(html)
    else:
        rates = parse_cuantoestaeldolar(html)
        assert len(rates) == expected_count
        for rate in rates:
            assert 2.0 <= rate.buy_price <= 5.0
            assert 2.0 <= rate.sell_price <= 5.0
            assert rate.spread > 0


@pytest.mark.parametrize(
    "fixture,expected_count,should_fail",
    [
        ("happy_path.json", 3, False),
        ("malformed_data.json", 2, False),
        ("missing_data.json", 1, False),
        ("empty.json", 0, True),
    ],
)
def test_tkambio_parsing(fixture, expected_count, should_fail):
    data = load_json("tkambio", fixture)

    if should_fail:
        with pytest.raises(ValueError, match="No valid exchange rates"):
            parse_tkambio(data)
    else:
        rates = parse_tkambio(data)
        assert len(rates) == expected_count
        for rate in rates:
            assert 2.0 <= rate.buy_price <= 5.0
            assert 2.0 <= rate.sell_price <= 5.0
            assert rate.spread > 0


@pytest.mark.parametrize(
    "fixture,expected_count,should_fail",
    [
        ("happy_path.json", 1, False),
        ("malformed_data.json", 0, True),
        ("missing_data.json", 0, True),
        ("empty.json", 0, True),
    ],
)
def test_tucambista_parsing(fixture, expected_count, should_fail):
    data = load_json("tucambista", fixture)

    if should_fail:
        with pytest.raises(ValueError, match="No valid exchange rates"):
            parse_tucambista(data)
    else:
        rates = parse_tucambista(data)
        assert len(rates) == expected_count
        for rate in rates:
            assert 2.0 <= rate.buy_price <= 5.0
            assert 2.0 <= rate.sell_price <= 5.0
            assert rate.spread > 0


@pytest.mark.parametrize(
    "fixture,expected_count,should_fail",
    [
        ("happy_path.json", 1, False),
        ("malformed_data.json", 0, True),
        ("missing_data.json", 0, True),
    ],
)
def test_westernunion_parsing(fixture, expected_count, should_fail):
    data = load_json("westernunion", fixture)

    if should_fail:
        with pytest.raises(ValueError, match="No valid exchange rates"):
            parse_westernunion(data)
    else:
        rates = parse_westernunion(data)
        assert len(rates) == expected_count
        for rate in rates:
            assert 2.0 <= rate.buy_price <= 5.0
            assert 2.0 <= rate.sell_price <= 5.0
            assert rate.spread > 0


@pytest.mark.parametrize(
    "fixture,expected_count,should_fail",
    [
        ("happy_path.html", 1, False),
        ("malformed_data.html", 1, False),
        ("missing_data.html", 0, True),
        ("empty.html", 0, True),
    ],
)
def test_instakash_parsing(fixture, expected_count, should_fail):
    html = load_html("instakash", fixture)

    if should_fail:
        with pytest.raises(
            ValueError,
            match=r"Could not find the main rates container|No valid exchange rates",
        ):
            parse_instakash(html)
    else:
        rates = parse_instakash(html)
        assert len(rates) == expected_count
        for rate in rates:
            assert 2.0 <= rate.buy_price <= 5.0
            assert 2.0 <= rate.sell_price <= 5.0
            assert rate.spread > 0


@pytest.mark.parametrize(
    "fixture,expected_count,should_fail",
    [
        ("happy_path.json", 1, False),
        ("malformed_data.json", 0, True),
        ("missing_data.json", 0, True),
        ("empty.json", 0, True),
    ],
)
def test_srcambio_parsing(fixture, expected_count, should_fail):
    data = load_json("srcambio", fixture)

    if should_fail:
        with pytest.raises(ValueError, match="No valid exchange rates"):
            parse_srcambio(data)
    else:
        rates = parse_srcambio(data)
        assert len(rates) == expected_count
        for rate in rates:
            assert 2.0 <= rate.buy_price <= 5.0
            assert 2.0 <= rate.sell_price <= 5.0
            assert rate.spread > 0
