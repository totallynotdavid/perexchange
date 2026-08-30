# perexchange-cli

Local diagnostic CLI for `perexchange`. It is not published to PyPI.

## Install

From the repository root, install the workspace and run the CLI with:

```bash
uv sync --all-packages
uv run --package perexchange-cli perexchange fetch
```

To install the CLI directly in editable mode:

```bash
cd packages/cli
pip install -e .
```

## Commands

The CLI currently supports two commands:

```bash
perexchange fetch          Fetch and display current rates
perexchange help           Show usage information
```

`fetch` prints one block for each returned rate. Expected source failures are omitted by
the library and logged through the `perexchange` logger.

```bash
$ perexchange fetch
Fetching current exchange rates...
============================================================
CURRENT EXCHANGE RATES (N rates)
============================================================
cambiafx:
  Buy:  S/ 3.3650
  Sell: S/ 3.3790
  Spread: S/ 0.0140
```
