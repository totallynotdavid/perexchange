# perexchange-cli

A command-line front end for `perexchange`. It is not published to PyPI. Run it from the
repository root:

```bash
uv run --package perexchange-cli perexchange fetch
```

## Commands

```text
fetch    Fetch and display all current rates
help     Show usage information
```

`perexchange` with no command, `help`, `--help`, or `-h` prints the usage text. An unknown
command exits with status 1.

`fetch` prints one block per rate, sorted by `sell_price` from lowest to highest. The
first block is the cheapest place to buy. `Pays you` is `buy_price`, and `Charges you` is
`sell_price`. `Spread` is their difference. For each failed source, `fetch` prints
`Skipped <source>: <message>` to stderr.

```text
$ uv run --package perexchange-cli perexchange fetch
Fetching current exchange rates...
============================================================
CURRENT EXCHANGE RATES (31 rates)
============================================================
mercadocambiario (mercadocambiario):
  Pays you:     S/ 3.4310
  Charges you:  S/ 3.4410
  Spread: S/ 0.0100
```
