# perexchange site

The site shows the current PEN/USD rates, a converter, history charts and the library
docs. It is an [Astro](https://astro.build) site, live at
<https://perexchange.vercel.app>.

## How it works

A scheduled workflow runs [`tools/snapshot.py`](../tools/snapshot.py) every 15 minutes.
The tool calls `perexchange.fetch_rates_report()` once and writes two files:

- `latest.json`, the newest fetch.
- `history/YYYY-MM-DD.jsonl`, one more line per fetch, in the file for that UTC day.

The workflow commits both to the orphan `data` branch. The rates pages render on request
from that branch and Vercel caches each for 15 minutes. The docs pages are built once per
deploy. Each page is plain HTML with the figures and the SVG charts already in it. A small
script sorts the table, runs the converter and updates the "quoted N minutes ago" text.
Without scripts the page still shows every rate and chart.

A live API would fetch about 28 sites for each visitor and take around 8 seconds. A
snapshot is fetched once for everyone, and the pages are served from the cache.

The charts cover the last 30 days. The page reads at most that many history files.

The file formats are in [Open data](src/docs/data.md). Who may write the data branch, and
what a reader sees while a run is in progress, are in
[Architecture](../docs/architecture.md#site-data).

## Develop

Run these from the repository root with `mise`, or from `site/` with `bun`.

| Task                  | What it does                                      |
| --------------------- | ------------------------------------------------- |
| `mise run site-data`  | Fetch every source and record a snapshot.         |
| `mise run site-dev`   | Serve the site with live reload.                  |
| `mise run site-build` | Build into `site/dist`.                           |
| `mise run site-check` | Type-check, lint, format-check and run the tests. |

`bun run format:astro` formats the `.astro` files with Prettier, because oxfmt does not
read them. Prettier moves spaces around inline tags, so the build test checks that the
spaces in the rendered text survive.

The site reads the published `data` branch. `bun run dev` and `bun run preview` read
`site/data` instead, which is ignored by git. `bun run data` fills it. Set
`PEREXCHANGE_DATA` to read another directory, relative to `site/`.

The tests cover the data path. `tests/contract.test.ts` runs the real Python tool on a few
made-up quotes and reads its output with the loaders the site uses, so a change to the
format on either side fails a test. `tests/build.test.ts` builds the site from that
output, starts the server and requests the pages. The tool's own tests run it against the
captured source responses. The tests build into `site/.scratch`, because Astro cannot move
files across filesystems.

## Deploy

The site is the Vercel project `perexchange` in the `empiricalhq` team, connected to this
repository. A push to `master` deploys it, with no token or workflow. The project's root
directory is `site/`. [`vercel.json`](vercel.json) holds an `ignoreCommand` that skips the
deploy when the push changed nothing in `site/`, the READMEs or `docs/`, which the docs
pages render. A push to the `data` branch never deploys.

The workflow [`.github/workflows/site.yml`](../.github/workflows/site.yml) only records
snapshots. Only `master` records, whether the run is scheduled or started by hand.

Some exchange houses block the address ranges of GitHub-hosted runners. A snapshot then
lists them under `failures`. The site leaves their prices out, so it calls a price the
cheapest or the best only "among the houses that answered" and says which houses are
missing. The run prints a warning that names them. To fetch from a machine they accept,
register a self-hosted runner and set the repository variable `REFRESH_RUNNER` to its
labels as JSON, for example `["self-hosted","peru"]`.

[`vercel.json`](vercel.json) sets the response headers, including the content security
policy. The policy allows no inline script, so every script must be an external file.
