from perexchange.scrapers.base import ExchangeRateScraper
from perexchange.scrapers.cambioseguro import fetch_cambioseguro
from perexchange.scrapers.cuantoestaeldolar import fetch_cuantoestaeldolar
from perexchange.scrapers.tkambio import fetch_tkambio
from perexchange.scrapers.tucambista import fetch_tucambista
from perexchange.scrapers.westernunion import fetch_westernunion


ALL_SCRAPERS: list[ExchangeRateScraper] = [
    fetch_cuantoestaeldolar,
    fetch_tkambio,
    fetch_cambioseguro,
    fetch_tucambista,
    fetch_westernunion,
]

__all__ = [
    "ALL_SCRAPERS",
    "ExchangeRateScraper",
    "fetch_cambioseguro",
    "fetch_cuantoestaeldolar",
    "fetch_tkambio",
    "fetch_tucambista",
    "fetch_westernunion",
]
