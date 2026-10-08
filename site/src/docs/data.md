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
    { "source": "okane", "error_type": "HTTPStatusError", "message": "403 Forbidden" }
  ]
}
```

- `buy` is what the house pays for a dollar. `sell` is what it charges. Both are soles.
- `id` is the quote's name in lowercase with runs of other characters replaced by `-`. Two
  sources that list the same house share an id.
- `timestamp` is the source's own time when it gives one, and the fetch time otherwise.
- `failures` lists the sources that returned nothing in that fetch.

## History

Every fetch is also appended to one line of `history/YYYY-MM-DD.jsonl` on the
[`data` branch](https://github.com/totallynotdavid/perexchange/tree/data), named for the
UTC day of the fetch:

```json
{ "t": "2026-10-08T14:30:00Z", "r": { "cambiafx": [3.435, 3.458, 0] } }
```

Each price is `[buy, sell, minutes since the quote]`. A quote older than three hours is
left out of the charts and of the best prices on the home page.

## How fresh it is

A scheduled job fetches every source about every 15 minutes and publishes the result.
GitHub may delay a scheduled run, so the page shows the time of the fetch and warns when
it is more than an hour old.
