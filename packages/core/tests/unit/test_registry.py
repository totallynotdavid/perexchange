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


def test_source_for_name_returns_none_for_unknown_or_non_string_values():
    assert source_for_name("not registered") is None
    assert source_for_name(None) is None
