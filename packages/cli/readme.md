# perexchange-cli

A development-only CLI for `perexchange`. It is not published to PyPI.

## Run it

From the repository root:

```bash
uv sync --all-packages
uv run --package perexchange-cli perexchange help
uv run --package perexchange-cli perexchange fetch
```

Running `perexchange` without a command also prints the help text.

## Commands

```text
fetch    Fetch and display current rates
help     Show usage information
```

`fetch` prints one block for each returned rate, sorted by the price for buying USD:

```text
$ uv run --package perexchange-cli perexchange fetch
Fetching current exchange rates...
============================================================
CURRENT EXCHANGE RATES (N rates)
============================================================
cambiafx (cambiafx):
  Buy:  S/ 3.3650
  Sell: S/ 3.3790
  Spread: S/ 0.0140
```

The command leaves failed sources out of the rate list and prints one diagnostic for each
source that failed.
