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
from perexchange.scrapers.registry import get_scrapers
from perexchange.scrapers.srcambio import fetch_srcambio
from perexchange.scrapers.tkambio import fetch_tkambio
from perexchange.scrapers.tucambista import fetch_tucambista
from perexchange.scrapers.westernunion import fetch_westernunion


__all__ = [
    "ExchangeRateScraper",
    "fetch_cambiafx",
    "fetch_cambiodigital",
    "fetch_cambiomundial",
    "fetch_cambioseguro",
    "fetch_cambiosol",
    "fetch_chapacambio",
    "fetch_chaskidolar",
    "fetch_cuantoestaeldolar",
    "fetch_defiperu",
    "fetch_dichikash",
    "fetch_dinekash",
    "fetch_dolarex",
    "fetch_dollarhouse",
    "fetch_inkamoney",
    "fetch_inticambio",
    "fetch_kambioonline",
    "fetch_marketdollar",
    "fetch_masscambio",
    "fetch_mercadocambiario",
    "fetch_metafx",
    "fetch_moneyhouse",
    "fetch_moneyplus",
    "fetch_okane",
    "fetch_srcambio",
    "fetch_tkambio",
    "fetch_tucambista",
    "fetch_westernunion",
    "get_scrapers",
]
