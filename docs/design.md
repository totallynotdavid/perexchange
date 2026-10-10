# Site design

The rules the site's look follows, and the values that carry them. The values live in
[`site/src/styles/tokens.css`](../site/src/styles/tokens.css) and the layout in
[`site/src/styles/site.css`](../site/src/styles/site.css).

## What the site is for

perexchange publishes the PEN/USD rates that Peruvian exchange houses post. Three kinds of
page serve three readers.

| Page      | Reader                                                  | The page must                                                                                                       |
| --------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `/`       | Someone in Peru about to exchange dollars, on a phone   | Name the best house for their side, its rate and its age, rank the others, price an amount, and chart the best rate |
| `/house/` | The same person checking one house, or a developer      | Show both sides, where the house stands, its other rates, and the 24 hour, 7 day and 30 day history                 |
| `/docs/`  | A developer deciding whether to use the library or data | Render the README, API, CLI, architecture and open-data documents                                                   |

The product is a table of numbers that go stale. So the design does three things: it puts
one figure large, it writes every figure in one monospaced face with equal digit widths,
and it shows age in a colour of its own the moment a rate is late.

## Direction

A quiet, neutral surface with one accent. Colour carries status and nothing else: blue for
links and the "you pay" series, green for the best rate and the "you get" series, amber
for old data, red for a failed read. The only shadow is the 1 px one under a selected
switch.

## Tokens

Every colour is a `light-dark()` pair except `--chart-buy`, so the page follows the
browser's colour scheme with no script and no class. `color-scheme: light dark` is set on
`:root`. `--chart-buy` is one value in both schemes, and the contrast test checks it in
both.

### Type

| Token         | Value                                                        | Use                                              |
| ------------- | ------------------------------------------------------------ | ------------------------------------------------ |
| `--font-sans` | Geist Variable, a metric-matched Arial fallback, `system-ui` | Text. Self-hosted, so it does not depend on host |
| `--font-mono` | Geist Mono Variable, a metric-matched Courier fallback       | Every figure, so digits have equal widths        |

The fallback faces set `size-adjust` and the vertical overrides from the font files'
metrics, so the swap to the web font moves nothing.

| Use                    | Size and line height                            | Weight |
| ---------------------- | ----------------------------------------------- | ------ |
| Best-rate figure       | 44/48, from 40 rem 56/64; 44/48 on a house page | 500    |
| Page `h1`              | 22/26, from 62 rem 32/36                        | 500    |
| Section `h2`           | 20/28, from 62 rem 24/32                        | 500    |
| Body                   | 16/24                                           | 400    |
| Secondary text, tables | 14 and 15, in a 20 or 24 line                   | 400    |
| Labels, column heads   | 13/20                                           | 450    |
| Chart ticks            | 12, monospaced                                  | 400    |
| Prose                  | 16, line height 1.6                             | 400    |

Body text uses `-webkit-font-smoothing: antialiased` and
`text-rendering: optimizeLegibility`.

### Surfaces and lines

| Token              | Light               | Dark               | Use                      |
| ------------------ | ------------------- | ------------------ | ------------------------ |
| `--bg`             | `oklch(1 0 0)`      | `oklch(0.171 0 0)` | Page                     |
| `--bg-subtle`      | `oklch(0.979 …)`    | `oklch(0.198 0 0)` | Cards                    |
| `--bg-muted`       | `oklch(0.955 …)`    | `oklch(0.236 0 0)` | Row hover                |
| `--border`         | `oklch(0.8514 0 0)` | `oklch(0.269 0 0)` | Cards, head rules        |
| `--border-subtle`  | `oklch(0.922 0 0)`  | `oklch(0.239 0 0)` | Row rules                |
| `--border-control` | `oklch(0.62 0 0)`   | `oklch(0.52 0 0)`  | A text field's edge, 3:1 |

Lines are solid greys, so they keep their colour over a tinted card.

### Text

| Token            | Light     | Dark      | Use                     |
| ---------------- | --------- | --------- | ----------------------- |
| `--fg`           | `#282a30` | `#f7f8f8` | Body, figures           |
| `--fg-secondary` | `#3c4149` | `#d0d6e0` | Lede, table text        |
| `--fg-muted`     | `#6c6b74` | `#8a8f98` | Labels, meta line, ages |

### Accent and status

| Token                          | Light                    | Dark                         | Use                                                      |
| ------------------------------ | ------------------------ | ---------------------------- | -------------------------------------------------------- |
| `--accent`                     | `oklch(0.5 0.16 247.27)` | `oklch(0.787 0.128 230.318)` | Links, focus, the "you pay" line                         |
| `--positive`, `-bg`, `-border` | green                    | green                        | The best rate and its badge                              |
| `--warn`, `-bg`, `-border`     | amber                    | amber                        | Old data and the late-refresh notice                     |
| `--danger`, `-bg`, `-border`   | red                      | red                          | A failed read                                            |
| `--chart-buy`                  | `#27a644`                | `#27a644`                    | The "you get" line. Reaches 3:1 on both page backgrounds |

Each status has a pale fill and a slightly stronger border of the same hue: an 8% fill and
a 20% border. The status colour reads on its fill at 4.5:1.

### Shape and motion

| Token                                    | Value                                  | Use                                         |
| ---------------------------------------- | -------------------------------------- | ------------------------------------------- |
| `--radius-sm`, `--radius`, `--radius-lg` | 5, 8, 12 px                            | Badges, controls, cards                     |
| `--duration-quick`, `--duration`         | 100 ms, 160 ms                         | Hover and state transitions                 |
| `--ease`                                 | `cubic-bezier(0.25, 0.46, 0.45, 0.94)` | Every transition                            |
| `--container`, `--gutter`                | 69.5 rem, 1 rem                        | Page width and its side margin              |
| `--header-height`                        | 3.5 rem                                | The sticky header                           |
| `--control-height`                       | 2.75 rem, 2.25 rem with a mouse        | Touch target 44 px; a fine pointer is 36    |
| `--focus-width`, `--focus-offset`        | 2 px, 2 px                             | The focus ring, drawn in `--accent`         |
| `--progress-height`, `--progress-delay`  | 2 px, 200 ms                           | The pending bar; the delay skips fast loads |

The segmented control's track has a 2 px inset and a 10 px radius around 8 px items. The
selected item takes the page background, a border and a 1 px shadow. Under
`prefers-reduced-motion: reduce` every transition is cut to 0.01 ms.

The switch's radios are invisible, so focus is drawn on the track: when a radio matches
`:focus-visible`, the whole control gets the focus ring (`--focus-width` and
`--focus-offset` in `--accent`), the same ring every other focusable element has. A mouse
click shows no ring. The ring's `--accent` is held to 3:1 on both page backgrounds by the
contrast test.

## Contrast

`site/tests/contrast.test.ts` reads `tokens.css`, converts each colour, and fails when a
text pair drops under 4.5:1 or a control's edge or chart line under 3:1. The table lists
the pairs that matter most.

| Pair                            | Light | Dark  | Used for                |
| ------------------------------- | ----- | ----- | ----------------------- |
| `--fg` on `--bg`                | 14.34 | 17.94 | Body                    |
| `--fg-secondary` on `--bg`      | 10.27 | 13.07 | Lede, table text        |
| `--fg-muted` on `--bg`          | 5.26  | 5.88  | Labels, meta line       |
| `--fg-muted` on `--bg-muted`    | 4.61  | 5.12  | Age under a hovered row |
| `--accent` on `--bg`            | 5.85  | 10.03 | Links                   |
| `--accent` on `--bg-subtle`     | 5.51  | 9.55  | Links inside a card     |
| `--warn` on `--bg`              | 6.13  | 11.06 | An old age              |
| `--warn` on `--warn-bg`         | 5.86  | 9.70  | The late-refresh notice |
| `--danger` on `--danger-bg`     | 5.48  | 7.48  | An error card's heading |
| `--positive` on `--positive-bg` | 5.18  | 8.70  | The "best" badge        |
| `--border-control` on `--bg`    | 3.64  | 3.47  | A text field's edge     |
| `--chart-buy` on `--bg`         | 3.17  | 6.02  | The "you get" line      |

The two chart lines differ in dash as well as colour, so they stay apart without colour.

## Layout

The container is `min(100% - 2rem, 69.5rem)`. The page has three breakpoints, all
`min-width`:

| Breakpoint | What changes                                                                                                                               |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 40 rem     | Cards take more padding, the figure grows, the side switch stops filling the row, the chart's range switch moves beside its legend         |
| 52 rem     | The docs navigation moves from a row above the text to a column beside it                                                                  |
| 62 rem     | The rates panel becomes two columns: a sticky card with the best rate and the amount field, and the table. Headings take their larger size |

At 390 px nothing scrolls sideways. A row of the rate table is one link: its name covers
the row, so a thumb has a row-high target. Docs tables and code blocks scroll inside their
own box. The charts switch to a narrow drawing below 40 rem.

## The calculator

The home page prices an amount on each side of the spread. A house has two rates: the
**sell rate** is what it charges for US$1, and the **buy rate** is what it pays for US$1.
A person who buys dollars pays the sell rate. A person who sells dollars gets the buy
rate. Each panel says which one it lists: "Each rate is the house's sell rate: what it
charges you for US$1", and "Each rate is the house's buy rate: what it pays you for
US$1".

### Buying dollars

The panel's first control is a two-item switch, "Dollars to buy" and "Soles to spend",
over one amount field. The switch sets the field's label, "I want to buy" or "I have", and
its prefix, `US$` or `S/`.

| Mode           | The person types | The table shows                              | The saving is                                |
| -------------- | ---------------- | -------------------------------------------- | -------------------------------------------- |
| Dollars to buy | US$, default 200 | "You pay", soles at each house's sell rate   | How much less than the dearest house pays    |
| Soles to spend | S/, default 1000 | "You get", dollars at each house's sell rate | How many more dollars than the dearest gives |

The table is ordered by rate, cheapest first, so the dearest house is the last row. Its
columns are:

- The house.
- The sell rate, headed "you pay per US$1".
- The total, with a sub-line that names the amount: "S/ for US$200.00".
- The saving, headed "vs the dearest".

The cheapest house's total is green, and a house that matches the dearest shows "–" for
its saving.

A one-line summary under the field names the best house and the gap. It reads "US$200.00
costs S/ 691.00 at X. That is S/ 5.00 less than at Y, the dearest." When every house gives
the same result at the amount, the summary says so instead of naming a gap.

Each mode keeps its own amount. The page remembers the side, the mode and each amount in
`localStorage`. An empty store, an empty saved amount or a blocked store gives the
defaults.

### Rounding and limits

The arithmetic runs in whole cents.

- A typed amount is rounded to the nearest cent. Grouping commas, spaces and underscores
  are ignored.
- Soles to pay are rounded to the nearest cent.
- Dollars received are rounded down, because a house hands over whole cents and the figure
  never exceeds what the money buys.
- The saving is the difference between the two rounded results, so the figures on the page
  add up.
- Binary noise is removed before rounding: 690 soles at 3.45 is exactly US$200.00.
- The largest amount is 1,000,000,000.

| Input                        | The field | The summary says                               |
| ---------------------------- | --------- | ---------------------------------------------- |
| Empty                        | Normal    | Type an amount to see what each house charges. |
| Zero, or rounds to zero      | Red edge  | Type an amount above zero.                     |
| Letters, symbols, two points | Red edge  | Use digits only, for example 200 or 1,250.50.  |
| Above 1,000,000,000          | Red edge  | Type 1,000,000,000 or less.                    |

For these four inputs the table's total and saving columns show "–".

The server renders the page for the default US$200, so the table and the summary are
complete before any script runs. The script reads the saved mode and amount and replaces
the figures on every keystroke with the same function the server used.

### Selling dollars

The sell panel has one field, "Dollars to sell", and one line: "You get S/ …", the amount
times the best buy rate, rounded to the nearest cent. It has no default: the field shows
the placeholder "1,000", and the line stays empty until the field holds a valid amount. A
zero, an invalid or a too large amount gets the same red edge and the same hint as in the
buy panel, in the body type instead of the figure's mono.

## The best-rate chart

Each panel of the home page ends with a line chart of the best rate over time: the
cheapest sell rate on the buying side and the highest buy rate on the selling side. The
points are the runs the pipeline recorded in `history/`, one per run, so the chart needs
no storage of its own.

- A point is the best rate among the houses that were current in that run: a quote older
  than 24 hours does not count, and neither does a variant, a house's second rate such as
  "from US$5,000".
- The range switch has 7 days, 30 days and All, and starts on 7 days. A range counts back
  from the newest point. How many days All reads is in the
  [site README](../site/README.md).
- The line is a single series with one dot per point, drawn in SVG by `lib/chart.ts`, with
  a wide and a narrow drawing like the house charts. The legend names the series, and the
  chart's text description gives the current value with the range's low and high.
- The time axis labels ticks with a clock time when the chart covers up to a day and a
  half, with a date when the ticks are a day or more apart, and with both between.
- When the first and the last point are under two days apart, the chart is replaced by one
  sentence. A few hours of readings would read as a trend, so the page waits.

## States

Every page has the states below. The site loads no data in the browser: the server reads
the data and sends finished HTML. So the only wait a reader sees is the wait for the next
page.

### Pending

Every page is rendered on request, so a click on a link or the submit of a form can wait
on the server. Once either starts a request to a page of the site, `lib/pending.ts` sets
`data-pending` on `<html>` (and `aria-busy` on a submitted form). The stylesheet then
shows a 2 px bar of `--accent` crossing the header's lower edge and sets the cursor to
`progress`. The bar appears after `--progress-delay` (200 ms), so a fast answer shows
nothing. The mark clears when the new page replaces this one, when the browser restores
this page from memory on Back, and after 15 s if the navigation was cancelled.

A link or form that goes to another site, a jump within the page, a new tab, a download, a
dialog form, a click with a modifier key and an event another script already handled start
no wait and set no mark. Under `prefers-reduced-motion: reduce` the bar stops moving and
shows as a still line. Without scripts the browser's own loading indicator is all there
is. No page has a form today: the amount fields compute in the page, and the side, mode
and range switches are CSS.

### Cases

| Where                       | Condition                                | What shows                                                                                                      |
| --------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `/`                         | Rates are late                           | An amber notice with the age, and ages in amber. A script shows the notice if the open page ages into it        |
| `/`                         | A side has no current rate               | A dashed card pointing to the houses that could not be read, which opens by default                             |
| `/`                         | Some houses could not be read            | A disclosure naming each house and the reason                                                                   |
| `/`                         | The best rate spans under two days       | In place of the chart, one sentence: the chart appears once two days are recorded, and the first is from a date |
| `/`                         | No reading is recorded                   | In place of the chart, "No readings are recorded yet."                                                          |
| `/`                         | The amount is empty, zero, invalid, huge | A hint replaces the summary and the table's figures show "–". Zero, invalid and huge also turn the border red   |
| `/`, `/house/`              | `latest.json` cannot be read             | Status 503 and a red card with a "Try again" link                                                               |
| `/house/`                   | The history cannot be read               | The rates show; the chart area becomes a red card with a "Try again" link                                       |
| `/house/`                   | A range holds no reading, or one reading | A dashed card saying so, or a point and the sentence "One reading so far, so there is no line yet"              |
| `/house/` for an unknown id | The id is not in the snapshot            | Status 404 and the not-found page                                                                               |
| Any other address           | No such page                             | The not-found page with links to the rates and the docs                                                         |

Without scripts the page still shows every rate, the table priced for US$200 and the
chart. The amount fields stay hidden, because they cannot work, and the side and range
switches still work, because they are CSS.

## Checking a change

Run `bun run check` in `site/`. To look at the pages, run `bun run data` once and
`bun run dev`, then open the home page, a house page and a docs page in both colour
schemes at 1440, 768 and 390 px.
