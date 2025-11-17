# [monorepo]: perexchange

[![CodeQL](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/codeql.yml)
[![tests](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml/badge.svg)](https://github.com/totallynotdavid/perexchange/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/perexchange/graph/badge.svg?token=KYQVD9QU30)](https://codecov.io/gh/totallynotdavid/perexchange)

A small library and optional CLI for fetching Peruvian exchange rates. Only three runtime
dependencies: httpx, beautifulsoup4, and lxml.

## Install

Library:

```bash
pip install perexchange
```

CLI (optional):

```bash
cd pkg/cli
uv pip install -e .
```

## Use

Python:

```python
import perexchange as px

rates = await px.fetch_rates()
print(px.find_best_buy(rates))
```

CLI:

```bash
perexchange best-buy
```

## Hack

```bash
mise run test         # run tests
mise run lint-format  # lint + format
mise run build-core   # build wheel into dist/
```
