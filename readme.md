# [pkg]: perexchange

[![CodeQL](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml)
[![tests](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/perexchange/graph/badge.svg?token=KYQVD9QU30)](https://codecov.io/gh/totallynotdavid/perexchange)

Peruvian dollar exchange rates (from cuantoestaeldolar.pe). One file, three deps (httpx,
beautifulsoup4 and lxml), async. To install it, just run:

```
uv pip install perexchange
```

You can use it like this:

```python
import perexchange as px

rates = await px.fetch_rates()
px.find_best_buy(rates)     # ExchangeRate(name='Kambista', buy_price=3.725, …)
```

See quick examples on how to use it [examples.py](examples.py) or run
`python -m perexchange --help`.

## CLI

Arguments: `px best-buy | best-sell | top-buy | stats | fetch`

```bash
perexchange fetch       # Show all current rates
perexchange best-buy    # Best place to buy
perexchange best-sell   # Best place to sell
perexchange top-buy     # Top 5 places to buy
perexchange top-sell    # Top 5 places to sell
perexchange stats       # Show statistics
perexchange help        # Show help
```

## Functions

fetch_rates() -> list[ExchangeRate]  
find_best_buy(rates) -> ExchangeRate | None  
find_best_sell(rates) -> ExchangeRate | None  
get_top_n(rates, n=3, op='buy'|'sell') -> list[ExchangeRate]  
calculate_average(rates, op) -> float | None  
calculate_spread(rates) -> float | None

ExchangeRate has `.name`, `.buy_price`, `.sell_price`, `.spread`.
