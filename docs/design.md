# Site design

The rules the site's look follows, and the values that carry them. The values live in
[`site/src/styles/tokens.css`](../site/src/styles/tokens.css) and the layout in
[`site/src/styles/site.css`](../site/src/styles/site.css).

## What the site is for

perexchange publishes the PEN/USD rates that Peruvian exchange houses post. Three kinds of
page serve three readers.

| Page      | Reader                                                  | The page must                                                                                       |
| --------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `/`       | Someone in Peru about to exchange dollars, on a phone   | Name the best house for their side, its rate and its age, rank the others, and work out an amount   |
| `/house/` | The same person checking one house, or a developer      | Show both sides, where the house stands, its other rates, and the 24 hour, 7 day and 30 day history |
| `/docs/`  | A developer deciding whether to use the library or data | Render the README, API, CLI, architecture and open-data documents                                   |

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

| Where                       | Condition                                | What shows                                                                                               |
| --------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `/`                         | Rates are late                           | An amber notice with the age, and ages in amber. A script shows the notice if the open page ages into it |
| `/`                         | A side has no current rate               | A dashed card pointing to the houses that could not be read, which opens by default                      |
| `/`                         | Some houses could not be read            | A disclosure naming each house and the reason                                                            |
| `/`, `/house/`              | `latest.json` cannot be read             | Status 503 and a red card with a "Try again" link                                                        |
| `/house/`                   | The history cannot be read               | The rates show; the chart area becomes a red card with a "Try again" link                                |
| `/house/`                   | A range holds no reading, or one reading | A dashed card saying so, or a point and the sentence "One reading so far, so there is no line yet"       |
| `/house/` for an unknown id | The id is not in the snapshot            | Status 404 and the not-found page                                                                        |
| Any other address           | No such page                             | The not-found page with links to the rates and the docs                                                  |

Without scripts the page still shows every rate. The amount field stays hidden, because it
cannot work, and the side switch still works, because it is CSS.

## Checking a change

Run `bun run check` in `site/`. To look at the pages, run `bun run data` once and
`bun run dev`, then open the home page, a house page and a docs page in both colour
schemes at 1440, 768 and 390 px.
