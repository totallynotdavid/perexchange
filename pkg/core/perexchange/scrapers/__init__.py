from .cuantoestaeldolar import fetch_cuantoestaeldolar

ALL_SCRAPERS = [
    fetch_cuantoestaeldolar,
]

__all__ = ["fetch_cuantoestaeldolar", "ALL_SCRAPERS"]
