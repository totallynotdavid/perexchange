from collections.abc import Sequence

from perexchange.scrapers.base import ExchangeRateScraper
from perexchange.scrapers.cambioseguro import fetch_cambioseguro
from perexchange.scrapers.cuantoestaeldolar import fetch_cuantoestaeldolar
from perexchange.scrapers.tkambio import fetch_tkambio
from perexchange.scrapers.tucambista import fetch_tucambista
from perexchange.scrapers.westernunion import fetch_westernunion


_SCRAPERS: dict[str, ExchangeRateScraper] = {
    "cambioseguro": fetch_cambioseguro,
    "cuantoestaeldolar": fetch_cuantoestaeldolar,
    "tkambio": fetch_tkambio,
    "tucambista": fetch_tucambista,
    "westernunion": fetch_westernunion,
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
    "fetch_cambioseguro",
    "fetch_cuantoestaeldolar",
    "fetch_tkambio",
    "fetch_tucambista",
    "fetch_westernunion",
    "get_scrapers",
]
