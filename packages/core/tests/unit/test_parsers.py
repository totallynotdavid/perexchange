"""Parser contract tests for captured source responses.

Each registered source has one fixture and one `EXPECTED_RATES` row. The table
pins exact output, while shared cases reject malformed payloads and enforce the
registry-to-fixture mapping.
"""

import json

from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

from perexchange.models import ExchangeRate
from perexchange.retry import PARSE_ERRORS
from perexchange.scrapers.registry import get_sources, source_for_name


FIXTURES = Path(__file__).parent.parent / "fixtures"

# Keep each source's expected rates in parser output order. A row can contain multiple
# quotes when the source publishes tiers or comparisons.
EXPECTED_RATES: dict[str, list[tuple[str, float, float]]] = {
    "cambiafx": [("cambiafx", 3.365, 3.379)],
    "cambiodigital": [("cambiodigital", 3.34, 3.36)],
    "cambiomundial": [("cambiomundial", 3.351, 3.357)],
    "cambioseguro": [
        ("cambioseguro", 3.353, 3.373),
        ("cambioseguro_comparative", 3.3426, 3.3959),
        ("cambioseguro_paralelo", 3.3388, 3.3929),
    ],
    "cambiosol": [("cambiosol", 3.2, 3.6)],
    "chapacambio": [("chapacambio", 3.353, 3.388)],
    "chaskidolar": [("chaskidolar", 3.339, 3.367)],
    "cuantoestaeldolar": [
        ("CambiaFX", 3.35, 3.36),
        ("Test Uncovered House A", 3.31, 3.38),
    ],
    "defiperu": [("defiperu", 3.348, 3.367)],
    "dichikash": [("dichikash", 3.347, 3.357)],
    "dinekash": [("dinekash", 3.34, 3.37)],
    "dolarex": [("dolarex", 3.3, 3.5)],
    "dollarhouse": [("dollarhouse", 3.365, 3.372)],
    "inkamoney": [("inkamoney", 3.34, 3.36)],
    "inticambio": [("inticambio", 3.349, 3.357)],
    "kambioonline": [("kambioonline", 3.34, 3.36)],
    "marketdollar": [("marketdollar", 3.345, 3.37)],
    "masscambio": [("masscambio", 3.348, 3.37)],
    "mercadocambiario": [("mercadocambiario", 3.348, 3.362)],
    "metafx": [("metafx", 3.344, 3.362)],
    "moneyhouse": [("moneyhouse", 3.347, 3.354)],
    "moneyplus": [("moneyplus", 3.349, 3.357)],
    "okane": [("okane", 3.31, 3.38)],
    "srcambio": [("srcambio", 3.347, 3.36)],
    "tkambio": [
        ("tkambio", 3.348, 3.378),
        ("tkambio_5000", 3.351, 3.375),
        ("tkambio_10000", 3.352, 3.374),
    ],
    "tucambista": [("tucambista", 3.348, 3.375)],
    "westernunion": [("westernunion", 3.352, 3.374)],
}

# These fixtures cover parser behavior that a representative response does not exercise.
BRANCH_FIXTURES = {
    "cuantoestaeldolar-all-covered",
    "dollarhouse-stale-hidden-inputs",
}

# Reject malformed payloads instead of inventing a quote.
JSON_JUNK: list[Any] = [
    {},
    [],
    "",
    0,
    None,
    {"unexpected": "shape"},
    [{"unexpected": "shape"}],
]
HTML_JUNK: list[Any] = ["", "<html></html>", "not markup at all"]


def fixture_path(stem: str) -> Path:
    matches = list(FIXTURES.glob(f"{stem}.*"))
    if len(matches) != 1:
        msg = f"expected exactly one fixture named {stem}.*, found {matches}"
        raise AssertionError(msg)
    return matches[0]


def load_fixture(stem: str) -> Any:
    path = fixture_path(stem)
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else text


def parser_for(source_name: str) -> Any:
    module = import_module(f"perexchange.scrapers.{source_name}")
    parsers = [
        parse
        for parse in (
            getattr(module, "_parse_json", None),
            getattr(module, "_parse_html", None),
        )
        if parse is not None
    ]
    if len(parsers) != 1:
        msg = f"{source_name} must expose exactly one parser, found {len(parsers)}"
        raise AssertionError(msg)
    return parsers[0]


def as_triples(rates: list[ExchangeRate]) -> list[tuple[str, float, float]]:
    return [(rate.name, rate.buy_price, rate.sell_price) for rate in rates]


def junk_cases() -> list[tuple[str, Any]]:
    junk_by_suffix = {".json": JSON_JUNK, ".html": HTML_JUNK}
    return [
        (source_name, junk)
        for source_name in sorted(EXPECTED_RATES)
        for junk in junk_by_suffix[fixture_path(source_name).suffix]
    ]


@pytest.mark.parametrize("source_name", sorted(EXPECTED_RATES))
def test_parses_captured_response(source_name):
    rates = parser_for(source_name)(load_fixture(source_name))

    assert as_triples(rates) == EXPECTED_RATES[source_name]
    for rate in rates:
        assert rate.source == source_name
        assert rate.buy_price < rate.sell_price, "buy and sell look swapped"
        assert rate.timestamp.tzinfo is not None, "timestamp must be aware"


@pytest.mark.parametrize(("source_name", "junk"), junk_cases())
def test_junk_payload_raises_instead_of_inventing_rates(source_name, junk):
    with pytest.raises(PARSE_ERRORS):
        parser_for(source_name)(junk)


def test_every_registered_source_has_a_case():
    registered = {source.id for source in get_sources()}

    assert registered == set(EXPECTED_RATES), (
        "every registered source needs a fixture and an EXPECTED_RATES row"
    )


def test_no_orphan_fixtures():
    on_disk = {path.stem for path in FIXTURES.iterdir()}

    assert on_disk == set(EXPECTED_RATES) | BRANCH_FIXTURES


def test_cuantoestaeldolar_parser_keeps_all_valid_houses():
    rates = parser_for("cuantoestaeldolar")(
        load_fixture("cuantoestaeldolar-all-covered")
    )

    assert as_triples(rates) == [
        ("CambiaFX", 3.35, 3.36),
        ("Tu Cambista", 3.34, 3.36),
    ]


@pytest.mark.parametrize(
    ("display_name", "expected"),
    [("CambiaFX", True), ("kambio online 2", True), ("Uncovered House", False)],
)
def test_aggregator_name_matching_uses_registry_aliases(display_name, expected):
    assert (source_for_name(display_name) is not None) is expected


def test_dollarhouse_prefers_displayed_rates_over_stale_hidden_inputs():
    # The page contains stale hidden inputs and current visible rates. The visible block
    # is what customers see and must win.
    rates = parser_for("dollarhouse")(load_fixture("dollarhouse-stale-hidden-inputs"))

    assert as_triples(rates) == [("dollarhouse", 3.365, 3.372)]
