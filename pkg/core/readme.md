# [pkg]: perexchange

Core library for fetching and analyzing Peruvian dollar (PEN-USD) exchange rates from
different exchange houses.

## Installation

```bash
pip install perexchange
```

## Usage

```python
import asyncio
from perexchange import fetch_rates, find_best_buy, find_best_sell

async def main():
    # Fetch current exchange rates
    rates = await fetch_rates()

    # Find best places to buy/sell
    best_buy = find_best_buy(rates)
    best_sell = find_best_sell(rates)

    print(f"Best buy: {best_buy.name} at S/ {best_buy.buy_price:.4f}")
    print(f"Best sell: {best_sell.name} at S/ {best_sell.sell_price:.4f}")

asyncio.run(main())
```

## API Reference

Core functions:

- `fetch_rates(scrapers=None)` - Fetch rates from all scrapers or specified ones
- `fetch_cuantoestaeldolar()` - Fetch rates from cuantoestaeldolar.pe

Analysis functions:

- `find_best_buy(rates)` - Find exchange house with lowest buy price
- `find_best_sell(rates)` - Find exchange house with highest sell price
- `get_top_n(rates, n=3, operation="buy")` - Get top N exchange houses
- `calculate_average(rates, operation="buy")` - Calculate average price
- `calculate_spread(rates)` - Calculate average spread
- `filter_by_price_range(rates, operation, min_price, max_price)` - Filter by price range

Data model:

- `ExchangeRate` - Dataclass with name, buy_price, sell_price, timestamp, and spread
  property
