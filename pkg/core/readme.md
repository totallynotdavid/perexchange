# [pkg]: perexchange

Core library for fetching PEN-USD exchange rates from Peruvian exchange houses. To install
it, run:

```bash
pip install perexchange
```

The library provides a single async function that fetches rates from multiple sources
concurrently:

```python
import asyncio
import perexchange as px

async def main():
    rates = await px.fetch_rates()
    best = min(rates, key=lambda r: r.buy_price)
    print(f"{best.name}: S/{best.buy_price}")

asyncio.run(main())
```

## Fetching rates

Call `fetch_rates()` to retrieve current rates. By default it queries all available
sources: cambioseguro, cuantoestaeldolar, tkambio, tucambista, and westernunion. The
function returns a list of `ExchangeRate` objects.

```python
rates = await px.fetch_rates()
```

You can fetch from specific sources by passing a list of house names. This is useful when
you only need rates from certain providers or want to reduce latency:

```python
rates = await px.fetch_rates(houses=["tkambio", "tucambista"])
```

The function accepts timeout and retry parameters. Timeout applies per house, not to the
entire operation. Retries only trigger on network errors, not parsing failures:

```python
rates = await px.fetch_rates(timeout=15.0, max_retries=5)
```

Failed sources are silently skipped. The function returns whatever rates it successfully
fetched, or an empty list if everything fails. Network errors trigger automatic retries
with exponential backoff. Parsing errors fail immediately.

## Working with rates

Each `ExchangeRate` contains the house name, buy and sell prices, and a UTC timestamp. Buy
price is what you pay in soles to buy dollars. Sell price is what you receive in soles
when selling dollars. The object is a frozen dataclass:

```python
rate = rates[0]
name = rate.name
buy = rate.buy_price
sell = rate.sell_price
when = rate.timestamp
spread = rate.spread
```

The spread property returns the difference between sell and buy prices. Some sources
return multiple tiers with different rates based on transaction amount, like
`tkambio_5000` and `tkambio_10000`.

Find the best rates by sorting or filtering the list:

```python
best_buy = min(rates, key=lambda r: r.buy_price)
best_sell = max(rates, key=lambda r: r.sell_price)
recent = [r for r in rates if (datetime.now(timezone.utc) - r.timestamp).seconds < 300]
```

## Error handling

Invalid house names raise `ValueError` immediately. All other failures are silent. Check
the returned list to see what succeeded:

```python
try:
    rates = await px.fetch_rates(houses=["nonexistent"])
except ValueError as e:
    print(f"Unknown house: {e}")

rates = await px.fetch_rates()
if not rates:
    print("All sources failed")
```

The library doesn't distinguish between different failure types. A house might fail due to
network issues, API changes, or parsing errors. Failed requests don't pollute your results
or logs.
