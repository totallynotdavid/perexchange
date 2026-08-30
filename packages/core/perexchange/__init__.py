from perexchange._version import __version__
from perexchange.core import fetch_rates, fetch_rates_report
from perexchange.errors import ConfigurationError
from perexchange.models import ExchangeRate, FetchReport, SourceFailure


__all__ = [
    "ConfigurationError",
    "ExchangeRate",
    "FetchReport",
    "SourceFailure",
    "__version__",
    "fetch_rates",
    "fetch_rates_report",
]
