from perexchange.scrapers.factories import digital_tc_parser, digital_tc_scraper


SOURCE = "srcambio"

_parse_json = digital_tc_parser(SOURCE)

fetch_srcambio = digital_tc_scraper(SOURCE, "sr-cambio", _parse_json)
