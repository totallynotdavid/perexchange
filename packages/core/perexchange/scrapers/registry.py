import re
import unicodedata

from collections.abc import Sequence
from dataclasses import dataclass

from perexchange.errors import ConfigurationError
from perexchange.scrapers.base import ExchangeRateScraper
from perexchange.scrapers.cambiafx import fetch_cambiafx
from perexchange.scrapers.cambiodigital import fetch_cambiodigital
from perexchange.scrapers.cambiomundial import fetch_cambiomundial
from perexchange.scrapers.cambioseguro import fetch_cambioseguro
from perexchange.scrapers.cambiosol import fetch_cambiosol
from perexchange.scrapers.chapacambio import fetch_chapacambio
from perexchange.scrapers.chaskidolar import fetch_chaskidolar
from perexchange.scrapers.cuantoestaeldolar import fetch_cuantoestaeldolar
from perexchange.scrapers.defiperu import fetch_defiperu
from perexchange.scrapers.dichikash import fetch_dichikash
from perexchange.scrapers.dinekash import fetch_dinekash
from perexchange.scrapers.dolarex import fetch_dolarex
from perexchange.scrapers.dollarhouse import fetch_dollarhouse
from perexchange.scrapers.inkamoney import fetch_inkamoney
from perexchange.scrapers.inticambio import fetch_inticambio
from perexchange.scrapers.kambioonline import fetch_kambioonline
from perexchange.scrapers.marketdollar import fetch_marketdollar
from perexchange.scrapers.masscambio import fetch_masscambio
from perexchange.scrapers.mercadocambiario import fetch_mercadocambiario
from perexchange.scrapers.metafx import fetch_metafx
from perexchange.scrapers.moneyhouse import fetch_moneyhouse
from perexchange.scrapers.moneyplus import fetch_moneyplus
from perexchange.scrapers.okane import fetch_okane
from perexchange.scrapers.srcambio import fetch_srcambio
from perexchange.scrapers.tkambio import fetch_tkambio
from perexchange.scrapers.tucambista import fetch_tucambista
from perexchange.scrapers.westernunion import fetch_westernunion


__all__ = ["Source", "get_sources", "source_for_name"]


@dataclass(frozen=True, slots=True)
class Source:
    """The stable identity and fetcher for one exchange-house source."""

    id: str
    fetcher: ExchangeRateScraper
    aliases: tuple[str, ...] = ()
    is_aggregator: bool = False


_SOURCES = (
    Source("cambioseguro", fetch_cambioseguro),
    Source("cambiafx", fetch_cambiafx),
    Source("cambiodigital", fetch_cambiodigital),
    Source("cambiomundial", fetch_cambiomundial),
    Source("cambiosol", fetch_cambiosol),
    Source("chapacambio", fetch_chapacambio),
    Source("chaskidolar", fetch_chaskidolar),
    Source("cuantoestaeldolar", fetch_cuantoestaeldolar, is_aggregator=True),
    Source("defiperu", fetch_defiperu),
    Source("dichikash", fetch_dichikash),
    Source("dinekash", fetch_dinekash),
    Source("dolarex", fetch_dolarex),
    Source("dollarhouse", fetch_dollarhouse),
    Source("inkamoney", fetch_inkamoney),
    Source("inticambio", fetch_inticambio),
    Source("kambioonline", fetch_kambioonline, ("kambioonline2",)),
    Source("marketdollar", fetch_marketdollar),
    Source("masscambio", fetch_masscambio),
    Source("mercadocambiario", fetch_mercadocambiario),
    Source("metafx", fetch_metafx),
    Source("moneyhouse", fetch_moneyhouse),
    Source("moneyplus", fetch_moneyplus),
    Source("okane", fetch_okane),
    Source("srcambio", fetch_srcambio),
    Source("tkambio", fetch_tkambio),
    Source("tucambista", fetch_tucambista),
    Source("westernunion", fetch_westernunion),
)

_SOURCES_BY_ID = {source.id: source for source in _SOURCES}


def _normalize_name(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", ascii_name.lower())


_NAMES_TO_IDS = {
    _normalize_name(name): source.id
    for source in _SOURCES
    for name in (source.id, *source.aliases)
}


def source_for_name(name: str) -> str | None:
    """Return the source ID matching a source ID, alias, or display name."""
    if not isinstance(name, str):
        return None
    return _NAMES_TO_IDS.get(_normalize_name(name))


def get_sources(source_names: Sequence[str] | None = None) -> list[Source]:
    """Resolve selected source names while preserving their order."""
    if source_names is None:
        return list(_SOURCES)
    if isinstance(source_names, str):
        msg = "sources must be a sequence of source names, not a string"
        raise ConfigurationError(msg)

    sources: list[Source] = []
    seen: set[str] = set()
    for source_name in source_names:
        source_id = source_for_name(source_name)
        if source_id is None:
            available = ", ".join(source.id for source in _SOURCES)
            msg = f"Unknown source: {source_name!r}. Available: {available}"
            raise ConfigurationError(msg)
        if source_id in seen:
            msg = f"Source selected more than once: {source_name!r}"
            raise ConfigurationError(msg)
        seen.add(source_id)
        sources.append(_SOURCES_BY_ID[source_id])
    return sources
