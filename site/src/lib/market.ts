import { formatDay } from "./format.ts";
import type { Failure, Quote, Snapshot } from "./data.ts";
import { houseKey, houseName, isVariant } from "./houses.ts";

/**
 * A quote older than this is not ranked. A house that has not changed its rate in a day
 * is closed or has stopped publishing, and a closed house cannot be used now. A quote
 * carries its source's time when the source gives one and the fetch time otherwise.
 */
export const DEAD_AFTER_MINUTES = 24 * 60;

/** Past this age a rate is shown as old, though it is still ranked. */
export const OLD_AFTER_MINUTES = 3 * 60;

const MINUTE = 60_000;

/** The transaction direction used to select a rate. */
export type Side = "buy" | "sell";

/** Whole minutes from an ISO time to now. A time in the future counts as now. */
export function minutesSince(at: string, now: string | number): number {
  const age =
    ((typeof now === "string" ? Date.parse(now) : now) - Date.parse(at)) / MINUTE;
  return Math.max(0, Math.round(age));
}

export function isOld(minutes: number): boolean {
  return minutes >= OLD_AFTER_MINUTES;
}

export function ageMinutes(quote: Quote, now: string | number): number {
  return minutesSince(quote.timestamp, now);
}

/** Selects the rate relevant to a transaction direction. */
export function rateFor(quote: Quote, side: Side): number {
  return side === "buy" ? quote.sell : quote.buy;
}

/** Measures a quote's gap from the best rate for a transaction direction. */
export function gapToBest(quote: Quote, best: Quote, side: Side): number {
  const gap = side === "buy" ? quote.sell - best.sell : best.buy - quote.buy;
  return Math.max(0, Math.round(gap * 10_000) / 10_000);
}

/** Returns each house's current base rate. */
export function current(quotes: Quote[], now: string | number): Quote[] {
  return quotes.filter(
    (quote) => !isVariant(quote) && ageMinutes(quote, now) <= DEAD_AFTER_MINUTES,
  );
}

/** Ranks current base rates, preferring newer quotes when rates tie. */
export function rank(quotes: Quote[], side: Side, now: string | number): Quote[] {
  const sign = side === "buy" ? 1 : -1;
  return current(quotes, now).sort(
    (a, b) =>
      sign * (rateFor(a, side) - rateFor(b, side)) ||
      Date.parse(b.timestamp) - Date.parse(a.timestamp),
  );
}

export interface Place {
  place: number;
  of: number;
  /** Soles per US$1 worse than the best. Zero for the best, and for a tie with it. */
  gap: number;
}

/** Finds a quote's place among current base rates, or null when it is not ranked. */
export function placeOf(
  quotes: Quote[],
  quote: Quote,
  side: Side,
  now: string | number,
): Place | null {
  const ranked = rank(quotes, side, now);
  const best = ranked[0];
  if (best === undefined || !ranked.some((one) => one.id === quote.id)) {
    return null;
  }
  const better = ranked.filter((one) => gapToBest(quote, one, side) > 0).length;
  return { place: better + 1, of: ranked.length, gap: gapToBest(quote, best, side) };
}

/**
 * Calculates the proceeds of a transaction and rounds them to cents.
 */
export function proceeds(amount: number, side: Side, rate: number): number {
  const raw = side === "buy" ? amount / rate : amount * rate;
  return Math.round(raw * 100) / 100;
}

/** Parses a positive amount with optional grouping separators. */
export function parseAmount(text: string): number | null {
  const cleaned = text.replace(/[,\s_]/g, "");
  if (!/^\d*\.?\d+$|^\d+\.$/.test(cleaned)) {
    return null;
  }
  const amount = Number(cleaned);
  return Number.isFinite(amount) && amount > 0 ? amount : null;
}

export interface MissingSince {
  at: number;
  atLeast: boolean;
}

/** Finds when a source's current run of missing fetches began. */
export function missingSince(snapshots: Snapshot[], source: string): MissingSince | null {
  let at: number | null = null;
  for (const snapshot of [...snapshots].reverse()) {
    if (snapshot.missing === null) {
      return at === null ? null : { at, atLeast: true };
    }
    if (!snapshot.missing.includes(source)) {
      return at === null ? null : { at, atLeast: false };
    }
    at = snapshot.t;
  }
  return at === null ? null : { at, atLeast: true };
}

const REASONS: Record<Failure["reason"], string> = {
  blocked: "Blocks requests from our server",
  changed: "Changed its page, so we cannot read it",
  timeout: "Did not answer in time",
  error: "Its website returned an error",
  invalid: "Published a rate that pays more than it charges",
  unreachable: "Did not answer",
};

export interface MissingHouse {
  name: string;
  why: string;
}

function since(found: MissingSince | null): string {
  return found === null
    ? ""
    : ` since ${found.atLeast ? "at least " : ""}${formatDay(found.at)}`;
}

/**
 * The houses a person might look for and cannot find: those that returned nothing, and
 * those whose only rate is too old to rank. A house another listing still covers is not
 * missing.
 */
export function missingHouses(
  quotes: Quote[],
  failures: Failure[],
  snapshots: Snapshot[],
  now: string | number,
): MissingHouse[] {
  const covered = new Set(current(quotes, now).map((quote) => houseKey(quote.name)));
  const missing = new Map<string, MissingHouse>();

  for (const failure of failures) {
    const key = houseKey(failure.source);
    if (!covered.has(key)) {
      missing.set(key, {
        name: houseName(failure.source),
        why: `${REASONS[failure.reason]}${since(missingSince(snapshots, failure.source))}.`,
      });
    }
  }
  for (const quote of quotes) {
    const key = houseKey(quote.name);
    if (!isVariant(quote) && !covered.has(key) && !missing.has(key)) {
      missing.set(key, {
        name: houseName(quote.name),
        why: `Has not changed its rate since ${formatDay(Date.parse(quote.timestamp))}.`,
      });
    }
  }
  return [...missing.values()].sort((a, b) => a.name.localeCompare(b.name));
}

export interface HousePoint {
  t: number;
  buy: number;
  sell: number;
}

/** Returns a house's current rates over time. */
export function houseSeries(snapshots: Snapshot[], id: string): HousePoint[] {
  const points: HousePoint[] = [];
  for (const snapshot of snapshots) {
    const price = snapshot.prices[id];
    if (price !== undefined && price.ageMinutes <= DEAD_AFTER_MINUTES) {
      points.push({ t: snapshot.t, buy: price.buy, sell: price.sell });
    }
  }
  return points;
}
