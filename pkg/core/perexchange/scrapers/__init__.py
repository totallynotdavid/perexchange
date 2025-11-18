from perexchange.scrapers.cambioseguro import fetch_cambioseguro
from perexchange.scrapers.cuantoestaeldolar import fetch_cuantoestaeldolar
from perexchange.scrapers.tkambio import fetch_tkambio
from perexchange.scrapers.tucambista import fetch_tucambista


ALL_SCRAPERS = [
    fetch_cuantoestaeldolar,
    fetch_tkambio,
    fetch_cambioseguro,
    fetch_tucambista,
]

__all__ = [
    "ALL_SCRAPERS",
    "fetch_cambioseguro",
    "fetch_cuantoestaeldolar",
    "fetch_tkambio",
    "fetch_tucambista",
]
