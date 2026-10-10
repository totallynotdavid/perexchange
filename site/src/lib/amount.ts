import { formatMoney } from "./format.ts";

/** The largest amount accepted. It is far above any exchange and keeps cents exact. */
export const MAX_AMOUNT = 1_000_000_000;

export type Mode = "usd" | "pen";

export const DEFAULT_AMOUNT: Record<Mode, number> = { usd: 200, pen: 1000 };

export type Reading =
  | { kind: "ok"; amount: number }
  | { kind: "empty" | "zero" | "invalid" | "huge" };

/**
 * Hundredths of a unit, with the binary noise of a product removed first, so that 690
 * divided by 3.45 is exactly 200.00 and never 199.99.
 */
function hundredths(value: number): number {
  return Number((value * 100).toPrecision(15));
}

/**
 * Reads an amount with optional grouping separators, as typed in the field. Money has
 * cents, so the amount is rounded to the nearest cent.
 */
export function readAmount(text: string): Reading {
  const cleaned = text.replace(/[,\s_]/g, "");
  if (cleaned === "") {
    return { kind: "empty" };
  }
  if (!/^\d*\.?\d+$|^\d+\.$/.test(cleaned)) {
    return { kind: "invalid" };
  }
  const amount = Math.round(hundredths(Number(cleaned))) / 100;
  if (amount === 0) {
    return { kind: "zero" };
  }
  return amount > MAX_AMOUNT ? { kind: "huge" } : { kind: "ok", amount };
}

/** What `usd` dollars cost in soles at `rate`, in cents, rounded to the nearest cent. */
export function solesFor(usd: number, rate: number): number {
  return Math.round(hundredths(usd * rate));
}

/**
 * What `soles` buy in dollars at `rate`, in cents, rounded down. A house hands over
 * whole cents, so the figure is never more than the money buys.
 */
export function usdFor(soles: number, rate: number): number {
  return Math.floor(hundredths(soles / rate));
}

export interface Line {
  /** The result in cents: soles to pay, or dollars to receive. */
  cents: number;
  /** How far the result is from the dearest house's, in cents. Zero for the dearest. */
  edge: number;
}

/**
 * The result at each rate and its edge over the dearest rate. The edge is the
 * difference of the two rounded results, so the figures shown add up.
 */
export function compare(mode: Mode, amount: number, rates: number[]): Line[] {
  if (rates.length === 0) {
    return [];
  }
  const result = (rate: number) =>
    mode === "usd" ? solesFor(amount, rate) : usdFor(amount, rate);
  const reference = result(Math.max(...rates));
  return rates.map((rate) => {
    const cents = result(rate);
    return { cents, edge: Math.abs(cents - reference) };
  });
}

const money = (cents: number) => formatMoney(cents / 100);

export interface Row {
  rate: number;
  house: string;
}

export interface BuyView {
  heads: { total: string; totalNote: string; edge: string };
  /** One pair of cells per row, in the order of the rows. */
  cells: { total: string; edge: string }[];
  summary: string;
}

const NO_FIGURE = "–";

const HINTS: Record<Exclude<Reading["kind"], "ok">, string> = {
  empty: "Type an amount to see what each house charges.",
  zero: "Type an amount above zero.",
  invalid: "Use digits only, for example 200 or 1,250.50.",
  huge: `Type ${MAX_AMOUNT.toLocaleString("en-US")} or less.`,
};

/**
 * What the sell line says for an amount of dollars at the best buy `rate`. An empty field
 * says nothing, and any other amount that cannot be priced gets the same hint as the buy
 * panel.
 */
export function sellSummary(reading: Reading, rate: number): string {
  if (reading.kind === "ok") {
    return `You get S/ ${money(solesFor(reading.amount, rate))}`;
  }
  return reading.kind === "empty" ? "" : HINTS[reading.kind];
}

/**
 * What the buy table and its summary say for an amount. `rows` are the houses, cheapest
 * rate first. The server renders this for the default amount and the page renders it
 * again on every keystroke, so both say the same.
 */
export function buyView(mode: Mode, reading: Reading, rows: Row[]): BuyView {
  const usd = mode === "usd";
  const heads = {
    total: usd ? "You pay" : "You get",
    edge: usd ? "Saves" : "Extra",
    totalNote: "",
  };
  if (reading.kind !== "ok") {
    return {
      heads,
      cells: rows.map(() => ({ total: NO_FIGURE, edge: NO_FIGURE })),
      summary: HINTS[reading.kind],
    };
  }

  const entered = usd
    ? `US$${formatMoney(reading.amount)}`
    : `S/ ${formatMoney(reading.amount)}`;
  heads.totalNote = `${usd ? "S/" : "US$"} for ${entered}`;

  const lines = compare(
    mode,
    reading.amount,
    rows.map((row) => row.rate),
  );
  const cells = lines.map((line) => ({
    total: money(line.cents),
    edge: line.edge === 0 ? NO_FIGURE : money(line.edge),
  }));

  const rates = rows.map((row) => row.rate);
  const cheapest = rates.indexOf(Math.min(...rates));
  const dearest = rates.lastIndexOf(Math.max(...rates));
  const best = lines[cheapest];
  const cheapestRow = rows[cheapest];
  const dearestRow = rows[dearest];
  if (best === undefined || cheapestRow === undefined || dearestRow === undefined) {
    return { heads, cells, summary: "" };
  }

  const lead = usd
    ? `${entered} costs S/ ${money(best.cents)} at ${cheapestRow.house}.`
    : `${entered} buys US$${money(best.cents)} at ${cheapestRow.house}.`;
  const against = `than at ${dearestRow.house}, the dearest.`;
  const tail =
    rows.length === 1
      ? ""
      : best.edge === 0
        ? " Every house gives the same at this amount."
        : usd
          ? ` That is S/ ${money(best.edge)} less ${against}`
          : ` That is US$${money(best.edge)} more ${against}`;
  return { heads, cells, summary: lead + tail };
}
