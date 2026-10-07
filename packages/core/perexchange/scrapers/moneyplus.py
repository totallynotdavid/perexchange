from perexchange.scrapers.factories import digital_tc_parser, digital_tc_scraper


SOURCE = "moneyplus"

_parse_json = digital_tc_parser(SOURCE)

fetch_moneyplus = digital_tc_scraper(SOURCE, "money-plus", _parse_json)
