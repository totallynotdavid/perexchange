# perexchange site

The site shows who gives the best PEN/USD rate right now and how old that rate
is, with every house ranked below it, a page for the best rate's history, a page
and history chart for each house, and the library docs. It is an
[Astro](https://astro.build) site, live at <https://perexchange.vercel.app>.

## How it works

A workflow runs [`tools/collect.py`](../tools/collect.py), which calls
[`tools/snapshot.py`](../tools/snapshot.py) every 15 minutes. Each fetch calls
`perexchange.fetch_rates_report()` once and writes two files:

- `latest.json`, the newest fetch.
- `history/YYYY-MM-DD.jsonl`, one more line per fetch, in the file for that UTC
  day.

The collector commits both to the orphan `data` branch after each fetch. The
rates pages render on request from that branch and Vercel caches them
([Architecture](../docs/architecture.md#what-a-reader-sees)). The docs pages are
built once per deploy. Each page is plain HTML with the figures and the SVG
charts already in it. A small script keeps the ages true while the page is open,
and another remembers the side, the unit and the amount a visitor chose. Without
scripts the page still shows every rate and chart.

A house page charts the last 30 days and reads at most that many history files.
The history page at `/history/` reads every recorded day, up to 365, for the All
range of its best-rate chart, and the home page reads none. The look, from
colour tokens to the calculator and the error states, is in
[Site design](../docs/design.md).

The file formats are in [Open data](src/docs/data.md). Who may write the data
branch, and what a reader sees while a run is in progress, are in
[Architecture](../docs/architecture.md#site-data).

## Develop

Run these from the repository root.

| Command                      | What it does                               |
| ---------------------------- | ------------------------------------------ |
| `mise run data:site`         | Fetch every source and record a snapshot.  |
| `bun run --cwd site dev`     | Serve the site with live reload.           |
| `bun run --cwd site preview` | Serve the built site.                      |
| `bun run --cwd site build`   | Build into `site/dist`.                    |
| `mise run lint:site`         | Lint with oxlint and check `.astro` files. |
| `mise run typecheck:site`    | Type-check with `astro check`.             |
| `mise run test:site`         | Check colour contrast and run the tests.   |

`mise run fix:site` formats the `.astro` files with Prettier, because oxfmt does
not read them. Prettier moves spaces around inline tags, so the build test
checks that the spaces in the rendered text survive.

The site reads the published `data` branch. `dev` and `preview` read `site/data`
instead, which is ignored by git. `mise run data:site` fills it. Set
`PEREXCHANGE_DATA` to read another directory, relative to `site/`.

The tests cover the data path. `tests/contract.test.ts` runs the real Python
tool on a few made-up quotes and reads its output with the loaders the site
uses, so a change to the format on either side fails a test.
`tests/build.test.ts` builds the site from that output, starts the server and
requests the pages. The tool's own tests run it against the captured source
responses. `mise run test:site` also checks the contrast of the colour tokens in
both schemes. The tests build into `site/.scratch`, because Astro cannot move
files across filesystems.

## Deploy

The site is the Vercel project `perexchange`, connected to this repository. A
push to `master` deploys it, with no token or workflow. The project's root
directory is `site/`. [`vercel.json`](vercel.json) holds an `ignoreCommand` that
skips the deploy when the push changed nothing in `site/`, the root `README.md`,
`docs/` or `packages/cli/README.md`, which the docs pages render. A push to the
`data` branch never deploys.

The workflow
[`.github/workflows/snapshot.yml`](../.github/workflows/snapshot.yml) only
records snapshots. [Architecture](../docs/architecture.md#site-data) says what
starts a run. `uv run python tools/history_report.py --data-dir site/data`
prints how many snapshots each day holds and the gaps between them, for a
checkout of the `data` branch.

Some exchange houses block the address ranges of GitHub-hosted runners, and a
snapshot lists them as `blocked` [failures](src/docs/data.md#latest-snapshot).
The site lists them under "not compared", with the reason from the latest
snapshot. The run prints a warning that names them. To fetch from a machine they
accept, register a self-hosted runner and set the repository variable
`REFRESH_RUNNER` to its labels as JSON, for example `["self-hosted","peru"]`.

[`vercel.json`](vercel.json) sets the response headers, including the content
security policy. The policy allows no inline script, so every script must be an
external file.
