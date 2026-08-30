import re
import unicodedata

from collections.abc import Sequence

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


_SCRAPERS: dict[str, ExchangeRateScraper] = {
    "cambioseguro": fetch_cambioseguro,
    "cambiafx": fetch_cambiafx,
    "cambiodigital": fetch_cambiodigital,
    "cambiomundial": fetch_cambiomundial,
    "cambiosol": fetch_cambiosol,
    "chapacambio": fetch_chapacambio,
    "chaskidolar": fetch_chaskidolar,
    "cuantoestaeldolar": fetch_cuantoestaeldolar,
    "defiperu": fetch_defiperu,
    "dichikash": fetch_dichikash,
    "dinekash": fetch_dinekash,
    "dolarex": fetch_dolarex,
    "dollarhouse": fetch_dollarhouse,
    "inkamoney": fetch_inkamoney,
    "inticambio": fetch_inticambio,
    "kambioonline": fetch_kambioonline,
    "marketdollar": fetch_marketdollar,
    "masscambio": fetch_masscambio,
    "mercadocambiario": fetch_mercadocambiario,
    "metafx": fetch_metafx,
    "moneyhouse": fetch_moneyhouse,
    "moneyplus": fetch_moneyplus,
    "okane": fetch_okane,
    "srcambio": fetch_srcambio,
    "tkambio": fetch_tkambio,
    "tucambista": fetch_tucambista,
    "westernunion": fetch_westernunion,
}

_HOUSE_ALIASES = {"kambioonline2": "kambioonline"}


def _normalize_house_name(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", ascii_name.lower())


def is_registered_house(name: str) -> bool:
    """Return whether an aggregator display name maps to a registered house."""
    normalized = _normalize_house_name(name)
    return _HOUSE_ALIASES.get(normalized, normalized) in _SCRAPERS


def get_scrapers(
    houses: Sequence[str] | None = None,
) -> list[tuple[str, ExchangeRateScraper]]:
    """
    Get (house name, scraper) pairs for specified houses, or all if None.

    Names are normalized to lowercase and pairs preserve the requested order.

    Raises:
        ValueError: If a house name is not recognized
    """
    if houses is None:
        return list(_SCRAPERS.items())

    scrapers = []
    for house in houses:
        house_lower = house.lower()
        if house_lower not in _SCRAPERS:
            available = ", ".join(sorted(_SCRAPERS.keys()))
            msg = f"Unknown house: {house!r}. Available: {available}"
            raise ValueError(msg)
        scrapers.append((house_lower, _SCRAPERS[house_lower]))

    return scrapers
