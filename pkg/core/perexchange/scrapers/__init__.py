from perexchange.scrapers.cuantoestaeldolar import fetch_cuantoestaeldolar
from perexchange.scrapers.tkambio import fetch_tkambio


ALL_SCRAPERS = [
    fetch_cuantoestaeldolar,
    fetch_tkambio,
]

__all__ = ["ALL_SCRAPERS", "fetch_cuantoestaeldolar", "fetch_tkambio"]
