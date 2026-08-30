from collections.abc import Sequence

from perexchange.scrapers.base import ExchangeRateScraper
from perexchange.scrapers.cambiafx import fetch_cambiafx
from perexchange.scrapers.cambioseguro import fetch_cambioseguro
from perexchange.scrapers.chapacambio import fetch_chapacambio
from perexchange.scrapers.cuantoestaeldolar import fetch_cuantoestaeldolar
from perexchange.scrapers.dollarhouse import fetch_dollarhouse
from perexchange.scrapers.instakash import fetch_instakash
from perexchange.scrapers.srcambio import fetch_srcambio
from perexchange.scrapers.tkambio import fetch_tkambio
from perexchange.scrapers.tucambista import fetch_tucambista
from perexchange.scrapers.westernunion import fetch_westernunion
from perexchange.scrapers.yanki import fetch_yanki


_SCRAPERS: dict[str, ExchangeRateScraper] = {
    "cambioseguro": fetch_cambioseguro,
    "cambiafx": fetch_cambiafx,
    "chapacambio": fetch_chapacambio,
    "cuantoestaeldolar": fetch_cuantoestaeldolar,
    "dollarhouse": fetch_dollarhouse,
    "instakash": fetch_instakash,
    "srcambio": fetch_srcambio,
    "tkambio": fetch_tkambio,
    "tucambista": fetch_tucambista,
    "westernunion": fetch_westernunion,
    "yanki": fetch_yanki,
}


def get_scrapers(houses: Sequence[str] | None = None) -> list[ExchangeRateScraper]:
    """
    Get scrapers for specified houses, or all if None.

    Raises:
        ValueError: If a house name is not recognized
    """
    if houses is None:
        return list(_SCRAPERS.values())

    scrapers = []
    for house in houses:
        house_lower = house.lower()
        if house_lower not in _SCRAPERS:
            available = ", ".join(sorted(_SCRAPERS.keys()))
            msg = f"Unknown house: {house!r}. Available: {available}"
            raise ValueError(msg)
        scrapers.append(_SCRAPERS[house_lower])

    return scrapers


__all__ = [
    "ExchangeRateScraper",
    "fetch_cambiafx",
    "fetch_cambioseguro",
    "fetch_chapacambio",
    "fetch_cuantoestaeldolar",
    "fetch_dollarhouse",
    "fetch_instakash",
    "fetch_srcambio",
    "fetch_tkambio",
    "fetch_tucambista",
    "fetch_westernunion",
    "fetch_yanki",
    "get_scrapers",
]
