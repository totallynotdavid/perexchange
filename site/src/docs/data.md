# Open data

The site is built from snapshots of `perexchange.fetch_rates_report()`, and the newest one
is public.

## Latest snapshot

`/data/latest.json` holds the newest fetch. Any website may read it.

```json
{
  "generated_at": "2026-10-08T14:30:00Z",
  "library_version": "2.0.0",
  "rates": [
    {
      "id": "cambiafx",
      "source": "cambiafx",
      "name": "cambiafx",
      "buy": 3.435,
      "sell": 3.458,
      "timestamp": "2026-10-08T14:29:48Z"
    }
  ],
  "failures": [
    {
      "source": "okane",
      "reason": "blocked",
      "error_type": "HTTPStatusError",
      "message": "Client error '403 Forbidden'"
    }
  ]
}
```

- `buy` is what the house pays for a dollar. `sell` is what it charges. Both are soles.
- `id` is the quote's name in lowercase with runs of other characters replaced by `-`. Two
  sources that list the same house share an id.
- `timestamp` is the source's own time when it gives one, and the fetch time otherwise.
- `failures` lists what gave no usable rate in that fetch, with the first line of the
  error as `message`. `reason` is one of `blocked` (the source refused our address with
  401, 403 or 429), `changed` (its page no longer parses), `timeout`, `error` (another
  HTTP error), `unreachable` (no answer at all) and `invalid` (the source answered, but
  its quote pays more than it charges). The site reads a missing or unknown `reason` as
  `error`.
- A quote that pays more than it charges is a source error, not a rate. It is left out of
  `rates` and listed in `failures` with the reason `invalid`. Its `source` is the name of
  the quote, not the ID of the source, because the answer was received and only the quote
  is rejected.

## History

Every fetch is also appended to one line of `history/YYYY-MM-DD.jsonl` on the
[`data` branch](https://github.com/totallynotdavid/perexchange/tree/data), named for the
UTC day of the fetch:

```json
{ "t": "2026-10-08T14:30:00Z", "r": { "cambiafx": [3.435, 3.458, 0] }, "f": ["okane"] }
```

Each price is `[buy, sell, minutes since the quote]`. `f` lists the `source` of every
entry in that fetch's `failures`, so it includes a quote rejected as `invalid`. Lines
recorded before `f` existed do not have it.

## How fresh it is

The age of a rate is the time from its `timestamp` to now. The site ranks only rates with
an age of 24 hours or less, because a house that has not updated its quote in a day is
closed or has stopped publishing. It shows an age of three hours or more as old, and it
warns when the whole snapshot is three hours old.

A job fetches every source and publishes the result. The
[architecture](../../../docs/architecture.md#site-data) lists what starts it. GitHub runs
scheduled jobs when it has capacity, so the gap between runs is often several hours. The
page therefore counts each age from now, not from the time of the fetch.
