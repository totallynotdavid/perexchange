import type { Quote } from "./data.ts";

/** `sell-usd` hands the house dollars for soles. `buy-usd` pays soles for dollars. */
export type Direction = "sell-usd" | "buy-usd";

/**
 * Reads what a person types into an amount box. Thousands separators are allowed.
 * Returns null for anything that is not a positive finite number.
 */
export function parseAmount(text: string): number | null {
  const cleaned = text.replace(/[,\s_]/g, "");
  if (cleaned === "" || !/^\d*\.?\d+$|^\d+\.$/.test(cleaned)) {
    return null;
  }
  const amount = Number(cleaned);
  return Number.isFinite(amount) && amount > 0 ? amount : null;
}

/**
 * Selling dollars earns the house's `buy` price in soles for each. Buying dollars
 * costs its `sell` price in soles for each. Results round to cents.
 */
export function convert(amount: number, direction: Direction, quote: Quote): number {
  const raw = direction === "sell-usd" ? amount * quote.buy : amount / quote.sell;
  return Math.round(raw * 100) / 100;
}

/** The quote that gives the most for the amount: highest `buy`, or lowest `sell`. */
export function bestQuote(quotes: Quote[], direction: Direction): Quote | null {
  let best: Quote | null = null;
  for (const quote of quotes) {
    if (best === null) {
      best = quote;
    } else if (direction === "sell-usd" ? quote.buy > best.buy : quote.sell < best.sell) {
      best = quote;
    }
  }
  return best;
}
