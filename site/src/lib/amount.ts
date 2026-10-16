import { formatMoney, formatPrice } from "./format.ts";
import type { Side } from "./market.ts";

/** The largest amount accepted. It is far above any exchange and keeps cents exact. */
export const MAX_AMOUNT = 1_000_000_000;

/** The currency the person types the amount in. */
export type Unit = "usd" | "pen";

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

/**
 * The other currency's amount at `rate`, in cents. A person who receives it gets whole
 * cents rounded down, so the figure never exceeds what the money is worth. A person who
 * pays or gives it is charged to the nearest cent.
 */
export function convert(side: Side, unit: Unit, amount: number, rate: number): number {
  const exact = unit === "usd" ? amount * rate : amount / rate;
  const received = side === "buy" ? unit === "pen" : unit === "usd";
  return received ? Math.floor(hundredths(exact)) : Math.round(hundredths(exact));
}

export interface Row {
  rate: number;
  house: string;
}

/** What the answer says. The server renders it for no amount and the page again on each keystroke. */
export interface Answer {
  /** What the figure is: "You pay", or "Best rate per US$1" while there is no amount. */
  label: string;
  currency: string;
  figure: string;
  /** The line under the figure: the saving at the best house, or why there is no total. */
  note: string;
  /** One total per row, in the order of the rows. Empty strings while there is no total. */
  totals: string[];
  /** The total column's head and what it is for: "for US$200.00". */
  head: { label: string; for: string };
}

/** Empty input has no hint because it is not an error. */
const HINTS: Record<Exclude<Reading["kind"], "ok" | "empty">, string> = {
  zero: "Type an amount above zero.",
  invalid: "Use digits only, for example 200 or 1,250.50.",
  huge: `Type ${MAX_AMOUNT.toLocaleString("en-US")} or less.`,
};

const money = (cents: number) => formatMoney(cents / 100);

function labels(side: Side, unit: Unit): { total: string; currency: string } {
  if (unit === "usd") {
    return { total: side === "buy" ? "You pay" : "You get", currency: "S/" };
  }
  return { total: side === "buy" ? "You get" : "You sell", currency: "US$" };
}

/**
 * What the hero and the table say for an amount on one side. `rows` are the houses, best
 * rate first, so the first row is the best deal and the last row the worst.
 */
export function answer(side: Side, unit: Unit, reading: Reading, rows: Row[]): Answer {
  const { total, currency } = labels(side, unit);
  const best = rows[0];
  const worst = rows.at(-1);
  const head = { label: total, for: "" };
  if (best === undefined || worst === undefined || reading.kind !== "ok") {
    return {
      label: "Best rate per US$1",
      currency: "S/",
      figure: best === undefined ? "" : formatPrice(best.rate),
      note: reading.kind === "ok" || reading.kind === "empty" ? "" : HINTS[reading.kind],
      totals: rows.map(() => ""),
      head,
    };
  }

  const entered =
    unit === "usd"
      ? `US$${formatMoney(reading.amount)}`
      : `S/ ${formatMoney(reading.amount)}`;
  head.for = side === "sell" && unit === "pen" ? `to get ${entered}` : `for ${entered}`;

  const cents = rows.map((row) => convert(side, unit, reading.amount, row.rate));
  const top = cents[0] ?? 0;
  const edge = Math.abs(top - (cents.at(-1) ?? top));
  const received = side === "buy" ? unit === "pen" : unit === "usd";
  const note =
    rows.length === 1
      ? ""
      : edge === 0
        ? "Every house gives the same at this amount."
        : `${currency} ${money(edge)} ${received ? "more" : "less"} than at ${worst.house}, which ${
            side === "buy" ? "charges the most" : "pays the least"
          }.`;
  return {
    label: total,
    currency,
    figure: money(top),
    note,
    totals: cents.map(money),
    head,
  };
}

/**
 * The amount to show in the field after the unit flips: what the typed amount is worth in
 * the other currency at the best rate. A field that holds no amount stays as it is.
 */
export function flipped(
  side: Side,
  unit: Unit,
  text: string,
  bestRate: number | undefined,
): string {
  const reading = readAmount(text);
  if (reading.kind !== "ok" || bestRate === undefined) {
    return text;
  }
  const cents = convert(side, unit, reading.amount, bestRate);
  return cents === 0 ? "" : (cents / 100).toFixed(2);
}
