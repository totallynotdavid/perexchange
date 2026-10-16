import pytest

from perexchange.errors import ConfigurationError
from perexchange.scrapers.registry import get_sources, source_for_name


def test_selected_sources_keep_caller_order_and_resolve_aliases():
    sources = get_sources(["tucambista", "kambioonline2"])

    assert [source.id for source in sources] == ["tucambista", "kambioonline"]


@pytest.mark.parametrize(
    "source_names",
    ["tucambista", ["kambioonline", "kambioonline2"]],
)
def test_invalid_source_selection_raises_configuration_error(source_names):
    with pytest.raises(ConfigurationError):
        get_sources(source_names)


@pytest.mark.parametrize(
    ("display_name", "registered"),
    [
        ("CambiaFX", True),
        ("kambio online 2", True),
        ("Uncovered House", False),
        ("not registered", False),
        (None, False),
    ],
)
def test_source_for_name_matches_registry_aliases(display_name, registered):
    assert (source_for_name(display_name) is not None) is registered
