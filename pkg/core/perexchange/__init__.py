"""
Fetch PEN-USD exchange rates from Peruvian exchange houses.

Example:
    >>> import perexchange as px
    >>> rates = await px.fetch_rates()
    >>> best = min(rates, key=lambda r: r.buy_price)
    >>> print(f"{best.name}: S/{best.buy_price}")
"""

from perexchange.core import fetch_rates
from perexchange.models import ExchangeRate


__version__ = "1.0.0"
__all__ = ["ExchangeRate", "fetch_rates"]
