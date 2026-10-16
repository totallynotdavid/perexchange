# Site design

The rules the site's look follows, and the values that carry them. The values live in
[`site/src/styles/tokens.css`](../site/src/styles/tokens.css) and the layout in
[`site/src/styles/site.css`](../site/src/styles/site.css).

## What the site is for

perexchange publishes the PEN/USD rates that Peruvian exchange houses post. Four kinds of
page serve three readers.

| Page        | Reader                                                  | The page must                                                                                         |
| ----------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `/`         | Someone in Peru about to exchange dollars, on a phone   | Take an amount, say what it costs or yields at the best house, send the reader there, rank the others |
| `/history/` | The same person, deciding whether to wait               | Chart how the best rate to buy and to sell has moved, on its own page so the board stays short        |
| `/house/`   | The same person checking one house, or a developer      | Show both sides, where the house stands, its other rates, and the 24 hour, 7 day and 30 day history   |
| `/docs/`    | A developer deciding whether to use the library or data | Render the README, API, CLI, architecture and open-data documents                                     |

The reader's question is "where do I get the best deal, and how many soles is it?". The
home page answers it in one path: type an amount, read the total at the best house, go to
that house. So the design does four things: the amount field comes first and has focus,
the answer to the amount is the one large figure, the one filled button leads to the
house, and the age of that rate sits directly under the button, in a colour of its own
only when the rate is old. Every figure is written in one monospaced face with equal digit
widths.

## Pages

Every page has the same header and footer. The header holds the brand and four links:
Rates, History, Docs and GitHub, with the current page marked. The GitHub link is hidden
below 40 rem. The open data's own document is in the docs navigation, so the header and
footer do not repeat it. The footer is one sentence: "Rates are what each house publishes,
not offers."

A page says only what a reader needs to act on. The page's name is its `h1`, and nothing
above it repeats the name. A number or age is shown once, where the reader decides with
it. A message appears when the reader must do something because of it: the rate is old, a
house is missing, a read failed.

### `/`

On a phone the first screen, with no scrolling, is the side switch, the amount field, the
best house for that side with its rate, the button that leads to it, and how old the rate
is. The blocks, in order:

1. The `h1`, "Dollar rates in Peru".
2. The card: the side switch, the amount field, the answer (the best rate and the house),
   the button, and under it "Rate from 15 min ago". When that rate is 3 hours old or more,
   a second line asks the reader to check it with the house before going.
3. The `h2` "26 houses, cheapest first" (or "highest payout first" on the selling side)
   and the table of the first five houses, with the rest behind "Show the other 21
   houses".
4. "1 house is not compared", a disclosure that names each house and why. It shows only
   when a house could not be read.

At 62 rem and wider the card is a sticky column beside the table, and the `h1` is above
both.

### `/history/`

1. The `h1`, "Best rate history".
2. The side switch, the same one as on `/`, set to the side the reader last chose.
3. The `h2` for the chosen side, "Cheapest price to buy US$1" or "Best price to sell
   US$1", and its chart.

### `/house/<id>/`

1. The `h1`, the house's name, with its special-rate label for a variant.
2. The age of the house's rate, then the button to the house's own site.
3. Two cards, the price to buy and the price to sell, each with where the house stands.
4. "Other rates from X", when the house has special rates or a standard one besides this.
5. The `h2` "Rate history" and its chart with a legend, the 24 hour, 7 day and 30 day
   range switch and a sentence per series.

### `/docs/`

The docs navigation beside the text on a wide screen and above it on a narrow one, then
the rendered document.

## Direction

A quiet, neutral surface with one accent. Colour carries status and nothing else: blue for
links, the button that leads to a house and the "you pay" series, green for the best total
and the "you get" series, amber for old data, red for a failed read. Panels have a light
shadow and the selected switch has the stronger 1 px shadow.

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

| Use                    | Size and line height           | Weight |
| ---------------------- | ------------------------------ | ------ |
| The answer             | 40/44, 56/64 from 40 to 62 rem | 500    |
| Best rate, house page  | 44/48, from 40 rem 56/64       | 500    |
| Page `h1`              | 28/32, 32/36 from 40 rem       | 500    |
| Section `h2`           | 20/28, from 62 rem 24/32       | 500    |
| Body                   | 16/24                          | 400    |
| Secondary text, tables | 14 and 15, in a 20 or 24 line  | 400    |
| Labels, column heads   | 13/20                          | 450    |
| Chart ticks            | 12, monospaced                 | 400    |
| Prose                  | 16, line height 1.6            | 400    |

Body text uses `-webkit-font-smoothing: antialiased` and
`text-rendering: optimizeLegibility`.

### Surfaces and lines

| Token              | Light               | Dark               | Use                      |
| ------------------ | ------------------- | ------------------ | ------------------------ |
| `--bg`             | `oklch(1 0 0)`      | `oklch(0.171 0 0)` | Page                     |
| `--bg-subtle`      | `oklch(0.979 …)`    | `oklch(0.198 0 0)` | Cards                    |
| `--bg-muted`       | `oklch(0.955 …)`    | `oklch(0.236 0 0)` | Row hover                |
| `--bg-strong`      | `oklch(0.94 …)`     | `oklch(0.266 0 0)` | Strong control surfaces  |
| `--border`         | `oklch(0.8514 0 0)` | `oklch(0.269 0 0)` | Cards, head rules        |
| `--border-subtle`  | `oklch(0.922 0 0)`  | `oklch(0.239 0 0)` | Row rules                |
| `--border-control` | `oklch(0.62 0 0)`   | `oklch(0.52 0 0)`  | A text field's edge, 3:1 |

Lines are solid greys, so they keep their colour over a tinted card.

### Text

| Token            | Light     | Dark      | Use              |
| ---------------- | --------- | --------- | ---------------- |
| `--fg`           | `#282a30` | `#f7f8f8` | Body, figures    |
| `--fg-secondary` | `#3c4149` | `#d0d6e0` | Lede, table text |
| `--fg-muted`     | `#6c6b74` | `#8a8f98` | Labels, ages     |

### Accent and status

| Token                        | Light                    | Dark                         | Use                                                      |
| ---------------------------- | ------------------------ | ---------------------------- | -------------------------------------------------------- |
| `--accent`                   | `oklch(0.5 0.16 247.27)` | `oklch(0.787 0.128 230.318)` | Links, focus, the button that leads to a house           |
| `--accent-soft`              | `oklch(0.96 0.025 247)`  | `oklch(0.246 0.025 247)`     | Quiet accent surfaces                                    |
| `--positive`                 | green                    | green                        | The best total in the table                              |
| `--warn`                     | amber                    | amber                        | An old rate and the advice to check it                   |
| `--danger`, `-bg`, `-border` | red                      | red                          | A failed read                                            |
| `--chart-buy`                | `#27a644`                | `#27a644`                    | The "you get" line. Reaches 3:1 on both page backgrounds |

An error has a pale fill and a slightly stronger border of the same hue: an 8% fill and a
20% border. The status colour reads on its fill at 4.5:1. A warning is text only, on the
page or card it belongs to.

### Shape and motion

| Token                                    | Value                                                        | Use                                         |
| ---------------------------------------- | ------------------------------------------------------------ | ------------------------------------------- |
| `--radius-sm`, `--radius`, `--radius-lg` | 5, 8, 12 px                                                  | Badges, controls, cards                     |
| `--duration-quick`, `--duration`         | 100 ms, 160 ms                                               | Hover and state transitions                 |
| `--ease`                                 | `cubic-bezier(0.25, 0.46, 0.45, 0.94)`                       | Every transition                            |
| `--shadow-panel`, `--shadow-selected`    | `0 1px 2px rgb(0 0 0 / 0.04)`, `0 1px 2px rgb(0 0 0 / 0.08)` | Panels and selected controls                |
| `--space-1` … `--space-12`               | 0.25, 0.5, 0.75, 1, 1.5, 2, 3 rem                            | Gaps and padding                            |
| `--container`, `--gutter`                | 84 rem, 1 rem                                                | Page width and its side margin              |
| `--header-height`                        | 3.5 rem                                                      | The sticky header                           |
| `--control-height`                       | 2.75 rem, 2.25 rem with a mouse                              | Touch target 44 px; a fine pointer is 36    |
| `--focus-width`, `--focus-offset`        | 2 px, 2 px                                                   | The focus ring, drawn in `--accent`         |
| `--progress-height`, `--progress-delay`  | 2 px, 200 ms                                                 | The pending bar; the delay skips fast loads |

The segmented control's track has a 2 px inset and a 10 px radius around 8 px items. The
selected item takes the page background, a border and `--shadow-selected`. Panels use
`--shadow-panel`. Under `prefers-reduced-motion: reduce` every transition is cut to 0.01
ms.

The switch's radios are invisible, so focus is drawn on the track: when a radio matches
`:focus-visible`, the whole control gets the focus ring (`--focus-width` and
`--focus-offset` in `--accent`), the same ring every other focusable element has. A mouse
click shows no ring. The ring's `--accent` is held to 3:1 on both page backgrounds by the
contrast test.

## Contrast

`site/tests/contrast.test.ts` reads `tokens.css`, converts each colour, and fails when a
text pair drops under 4.5:1 or a control's edge or chart line under 3:1. The table lists
the pairs that matter most.

| Pair                         | Light | Dark  | Used for                      |
| ---------------------------- | ----- | ----- | ----------------------------- |
| `--fg` on `--bg`             | 14.34 | 17.94 | Body                          |
| `--fg-secondary` on `--bg`   | 10.27 | 13.07 | Lede, table text              |
| `--fg-muted` on `--bg`       | 5.26  | 5.88  | Labels, ages                  |
| `--fg-muted` on `--bg-muted` | 4.61  | 5.12  | Details link on a hovered row |
| `--accent` on `--bg`         | 5.85  | 10.03 | Links                         |
| `--accent` on `--bg-subtle`  | 5.51  | 9.55  | Links inside a card           |
| `--bg` on `--accent`         | 5.85  | 10.03 | The button's label            |
| `--warn` on `--bg`           | 6.13  | 11.06 | A late rate                   |
| `--warn` on `--bg-subtle`    | 5.76  | 10.53 | The advice inside the card    |
| `--danger` on `--danger-bg`  | 5.48  | 7.48  | An error card's heading       |
| `--positive` on `--bg`       | 5.64  | 9.47  | The best total                |
| `--border-control` on `--bg` | 3.64  | 3.47  | A text field's edge           |
| `--chart-buy` on `--bg`      | 3.17  | 6.02  | The "you get" line            |

The two chart lines differ in dash as well as colour, so they stay apart without colour.

## Layout

The container is `min(100% - 2rem, 84rem)`. The page has three breakpoints, all
`min-width`:

| Breakpoint | What changes                                                                                                                                                                                         |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 40 rem     | Cards take more padding, the answer grows to 56/64, the chart's range switch moves beside its legend                                                                                                 |
| 52 rem     | The docs navigation moves from a row above the text to a column beside it                                                                                                                            |
| 62 rem     | The home page becomes two columns: a sticky card with the switch, the amount field, the answer and the button, and the table beside it. The answer returns to 40/44. Headings take their larger size |

At 390 px nothing scrolls sideways, and the card with the field, the answer and the button
fits the first screen, so the answer is in view without scrolling. Docs tables and code
blocks scroll inside their own box. The charts switch to a narrow drawing below 40 rem.

## The calculator

The home page is one card and one table. The card holds the direction switch, the amount
field, the answer and the button that leads to the house. The table ranks every house for
the same amount. The side's two rates are named in the reader's words: a house has a
**sell rate**, what it charges for US$1, and a **buy rate**, what it pays for US$1. A
person who buys dollars pays the sell rate and a person who sells them gets the buy rate,
and the page says "Rate per US$1" for whichever applies. The terms sell rate and buy rate
appear only in the library's documents.

### The card

1. A two-item switch, "I want to buy US$" and "I want to sell US$". It is the only
   direction control. The first item is chosen.
2. One amount field with focus. At its left edge a button shows the unit the amount is
   typed in, `US$` or `S/`, with a ⇄ mark. Pressing it flips the unit and rewrites the
   field to what the amount is worth in the other currency at the best house's rate, so
   US$200 becomes S/ 691.00. An empty or invalid field stays as it is. The field's label
   for assistive technology is "Amount to buy" or "Amount to sell", and the button's name
   says what it will change to: "US$, change to soles".
3. The answer, an `<output>` tied to the field, so a screen reader hears the total as it
   changes. Its parts are a label, the figure, the house, and a note.
4. The button, "Go to X", the one filled element on the page. It opens the house's own
   site in a new tab, where the house publishes its rate. A house whose site is not listed
   gets "See X", which opens the house's page on this site.

With no amount the answer is the best rate: the label "Best rate per US$1", the rate
large, and the house. The note is empty. There is no default amount, so the field shows
the placeholder "Amount" and nothing the reader did not type.

With an amount the label is the total's name and the figure is the total at the best
house, as in "You pay S/ 691.00 at Gordito digital". The note says what the choice saves,
once on the page: "S/ 5.40 less than at Kambio Online, which charges the most", or "more …
than at X, which pays the least" for a sum received. When every house gives the same, the
note says so, and for one house it is empty.

| Side | Unit | The total is | Its label and the table's head |
| ---- | ---- | ------------ | ------------------------------ |
| Buy  | US$  | S/ to pay    | You pay                        |
| Buy  | S/   | US$ received | You get                        |
| Sell | US$  | S/ received  | You get                        |
| Sell | S/   | US$ to sell  | You sell                       |

The note always compares with the worst house of the side: the one that charges the most
to a buyer, or pays the least to a seller.

Under the button the card always says how old the best house's rate is, "Rate from 15 min
ago", in the muted colour. Once that rate is 3 hours old or more, the age turns amber and
a second line, "Check it with the house before you go.", follows. A script updates both
while the page is open.

### The table

The table ranks the houses by rate, best first, and shows the first five. A disclosure,
"Show the other N houses", holds the rest in the same columns. Its columns are:

- **House.** The name is a link to the house's own site, and its target covers the whole
  row, so a thumb has a row-high target. A rate 3 hours or more older than the fetch adds
  the line "Rate from 5 h ago" in amber under the name. A fresh rate adds nothing, because
  the card gives the age of the best rate.
- **Rate per US$1.**
- **You pay**, **You get** or **You sell**, with a second line that names the amount, "for
  US$200.00" or "to get S/ 691.00". The best total is green. The column and its head
  appear only while the amount is valid.
- **Details**, a link to the house's page on this site.

The table's `h2` gives the count and the order, "14 houses, cheapest first". The count is
shown there and nowhere else.

The amount, the side and the unit are kept in `localStorage` under `perexchange:amount`,
`perexchange:side` and `perexchange:unit`. A blocked store or an empty one gives the
placeholder, the buy side and US$. A page that cannot write keeps the values until it
closes.

### Rounding and limits

The arithmetic runs in whole cents.

- A typed amount is rounded to the nearest cent. Grouping commas, spaces and underscores
  are ignored.
- An amount paid or given is rounded to the nearest cent.
- An amount received is rounded down, because a house hands over whole cents and the
  figure never exceeds what the money buys.
- The note is the difference between the two rounded results, so the figures on the page
  add up.
- Binary noise is removed before rounding: 690 soles at 3.45 is exactly US$200.00.
- The largest amount is 1,000,000,000.

| Input                        | The field | The note says                                 |
| ---------------------------- | --------- | --------------------------------------------- |
| Empty                        | Normal    | Nothing                                       |
| Zero, or rounds to zero      | Red edge  | Type an amount above zero.                    |
| Letters, symbols, two points | Red edge  | Use digits only, for example 200 or 1,250.50. |
| Above 1,000,000,000          | Red edge  | Type 1,000,000,000 or less.                   |

For these inputs the answer shows the best rate and the total column is hidden. The field
sets `aria-invalid` for the last three. The note reserves one line, empty or not.

The server renders the card for no amount and leaves the field hidden, so the best rate
and the full table are in the page before any script runs. The script shows the field,
restores the saved values, moves focus into it, and replaces the answer and the totals on
every keystroke with the same function the server used.

## The best-rate chart

The `/history/` page charts the best rate over time, one chart per side: the cheapest sell
rate on the buying side and the highest buy rate on the selling side. It has its own page
so the board stays short and the page that reads every recorded day is one a reader opens
on purpose. The side switch is the home page's, and the two pages share the choice in
`perexchange:side`. The points are the runs the pipeline recorded in `history/`, one per
run, so the chart needs no storage of its own.

- A point is the best rate among the houses that were current in that run: a quote older
  than 24 hours does not count, and neither does a variant, a house's second rate such as
  "from US$5,000".
- The range switch has 7 days, 30 days and All, and starts on 7 days. A range counts back
  from the newest point. How many days All reads is in the
  [site README](../site/README.md).
- The line is a single series with one dot per point, drawn in SVG by `lib/chart.ts`, with
  a wide and a narrow drawing like the house charts. A chart with several series has a
  legend; this one has none.
- One sentence above the line states the change as a number, such as "Up S/ 0.0050 (0.1%)
  in 7 days, from S/ 3.4500 to S/ 3.4550." The same sentence is the chart's text
  description. Nothing repeats it under the chart.
- The price axis spans at least 4% of the price, centred on the data, so a move of a cent
  or two reads as the small move it is. A larger move widens the axis to fit.
- The time axis ticks are whole days in Lima time when the chart covers more than a day
  and a half, and whole hours aligned to the step otherwise. A tick never shows a minute.
  There are up to 8 ticks on the wide drawing and 4 on the narrow one.
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
is. No page has a form today: the amount field computes in the page, and the side and
range switches are CSS.

### Cases

| Where                       | Condition                                | What shows                                                                                                      |
| --------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `/`                         | The best rate is old                     | The age under the button turns amber, and a line asks the reader to check the rate with the house               |
| `/`                         | One rate in the table is late            | The line "Rate from 5 h ago" in amber under the house's name                                                    |
| `/`                         | No house has a current rate              | A dashed card pointing to the houses that could not be read, which opens by default                             |
| `/`                         | Some houses could not be read            | A disclosure naming each house and the reason                                                                   |
| `/`                         | The amount is zero, invalid or huge      | The note gives a hint, the answer shows the best rate, the total column is hidden and the border turns red      |
| `/history/`                 | The best rate spans under two days       | In place of the chart, one sentence: the chart appears once two days are recorded, and the first is from a date |
| `/history/`                 | No reading is recorded                   | In place of the chart, "No readings are recorded yet."                                                          |
| `/history/`                 | The history cannot be read               | A red card with a "Try again" link                                                                              |
| `/`, `/history/`, `/house/` | `latest.json` cannot be read             | Status 503 and a red card with a "Try again" link                                                               |
| `/house/`                   | The history cannot be read               | The rates show; the chart area becomes a red card with a "Try again" link                                       |
| `/house/`                   | A range holds no reading, or one reading | A dashed card saying so, or a point and the sentence "One reading so far, so there is no line yet"              |
| `/house/` for an unknown id | The id is not in the snapshot            | Status 404 and the not-found page                                                                               |
| Any other address           | No such page                             | The not-found page with links to the rates and the docs                                                         |

Without scripts the page still shows the best rate per side, every rate in the table and
the charts. The amount field stays hidden, because it cannot work, and the side and range
switches still work, because they are CSS. The "Go to" button works too. Without scripts
the side switch starts on buying and does not remember a choice.

## Checking a change

Run `bun run check` in `site/`. To look at the pages, run `bun run data` once and
`bun run dev`, then open the home page, the history page, a house page and a docs page in
both colour schemes at 1440, 768 and 390 px.
