# [pkg]: perexchange

This package contains the core functionality for retrieving and analyzing Peruvian
exchange rates. It is the library published to PyPI.

To install the library, run:

```bash
pip install perexchange
```

Quick usage example:

```python
import asyncio
from perexchange import fetch_rates, find_best_buy, find_best_sell

async def main():
    rates = await fetch_rates()
    print(find_best_buy(rates))

asyncio.run(main())
```

## API Reference

Core Functions:

1. `fetch_rates(scrapers=None)` returns a list of `ExchangeRate` objects.
2. `find_best_buy(rates)` returns the entry with the lowest buy price.
3. `find_best_sell(rates)` returns the entry with the highest sell price.

Data Model:

```python
ExchangeRate
    name: str
    buy_price: float
    sell_price: float
    timestamp: datetime
    spread: float (sell_price - buy_price)
```

Internal functions:

```python
get_top_n(rates, n, operation)
calculate_average(rates, operation)
calculate_spread(rates)
filter_by_price_range(rates, operation, min_price, max_price)
```
