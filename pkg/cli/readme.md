# [pkg]: perexchange-cli

Command-line interface for perexchange. This tool is intended for local development and
diagnostics. It is not published to PyPI.

To install the library, run:

```bash
cd pkg/cli
pip install -e .
```

The CLI accepts these arguments:

```bash
perexchange best-buy       Show best place to buy USD
perexchange best-sell      Show best place to sell USD
perexchange top-buy        Show top N buy rates
perexchange top-sell       Show top N sell rates
perexchange stats          Show market statistics
perexchange fetch          Show all current rates
perexchange help           Show help
```

The results will look like this:

```bash
$ perexchange best-buy
Best Place To Buy
Exchange House: CambiaFX
Buy Price: S/ 3.3520
Timestamp: 2025-01-15 14:30:00+00:00
```

```bash
$ perexchange stats
Exchange Houses: 15
Average Buy Price: S/ 3.3650
Average Sell Price: S/ 3.3920
Best Buy: CambiaFX
Best Sell: Rextie
```
