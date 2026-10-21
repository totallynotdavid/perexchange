perexchange 2.1.0 is out.

It has been 52 days since 2.0.0. This is a minor release: it needs Python 3.12
or later and removes the `cambiodigital` source, which no longer worked.
Everything else is a fix or an addition. If you are on Python 3.12 or later and
do not name `cambiodigital`, upgrade.

The biggest fix is in the aggregator. Selecting `cuantoestaeldolar` alone used
to drop every row whose house has a source of its own, even when you had not
selected that source. Now you get a rate for every house it lists. A row is
dropped only when you also selected that house's own source and it returned
rates. If the house's own source failed, the aggregator's row stays.

Failures now say more, and a rate's age is now honest. `SourceFailure` has a new
`status_code` field, the HTTP status of an error response, so a `403` from a
house that blocks your address no longer looks like a broken parser. It is
`None` when the source did not answer. Three houses (`cambiomundial`,
`kambioonline`, `mercadocambiario`) stamped every quote with the fetch time, so
a rate that had not moved for days looked fresh. They, and `okane`, now use the
time the source reports.

A request error that is not an `httpx` error, such as the `h2` protocol error
that escaped in 3 of 5 live runs, is now retried and recorded as a failure of
that source. It used to fail the whole call. `srcambio` and `moneyplus` moved to
the shared platform API, because `moneyplus` served stale data from its legacy
endpoint. The platform reports Lima time without an offset, and it is now read
as UTC-5.

The rest is internal: the scraper factories no longer take a source ID, the code
uses Python 3.12 syntax, and there are new tests, a collector and report tools,
a rebuilt site, and docs. The `ExchangeRate` docstring and the examples now say
which side of a quote `buy_price` and `sell_price` are: `buy_price` is what the
house pays you, `sell_price` is what it charges.

## Python 3.12 and the removed source

2.1.0 requires Python 3.12 or later (`9f206dd`). Python 3.10 reaches end of life
this month and 3.11 in 2027. pip checks the requirement, so on Python 3.10 or
3.11 it keeps installing 2.0.0 and your code keeps working:

```bash
# on Python 3.10 or 3.11: installs 2.0.0, no pin needed
python3.11 -m pip install -U perexchange
```

The `cambiodigital` source is gone because its site is gone (`14a2243`). Its
endpoint returns 404 and has no replacement, so it already failed for every
caller. In 2.0.0 a call that named it got no rates and a `SourceFailure`. Now
naming it raises `ConfigurationError`, and a call without `sources` no longer
queries it:

```python
# 2.0.0: no rates, report.failures held a 404 for cambiodigital
await perexchange.fetch_rates(sources=["cambiodigital"])

# 2.1.0: raises ConfigurationError, "Unknown source: 'cambiodigital'"
await perexchange.fetch_rates(sources=["cambiafx", "tucambista"])
```

## Known problems

Some houses answer `403` to requests from cloud or datacenter addresses. They
show up in `report.failures` with `status_code == 403` and the rest of the call
still works. The workaround is to fetch from another address, such as a home or
office connection.

## What to do

Upgrade with `pip install -U perexchange`. Remove `cambiodigital` from any
`sources` list. If you run `fetch_rates_report()`, check `report.failures` after
the upgrade. Report problems at
https://github.com/totallynotdavid/perexchange/issues.
