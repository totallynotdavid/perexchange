from perexchange.scrapers.cuantoestaeldolar import fetch_cuantoestaeldolar


ALL_SCRAPERS = [
    fetch_cuantoestaeldolar,
]

__all__ = ["ALL_SCRAPERS", "fetch_cuantoestaeldolar"]
