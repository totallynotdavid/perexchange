import type { Failure, Quote, Snapshot } from "./data.ts";

/**
 * A quote older than this is listed but never ranked, because its house has stopped
 * updating it. A quote carries its source's time when the source gives one and the
 * fetch time otherwise, so only the first kind can go stale.
 */
export const STALE_AFTER_MINUTES = 180;

const MINUTE = 60_000;

export function ageMinutes(quote: Quote, generatedAt: string): number {
  const age = (Date.parse(generatedAt) - Date.parse(quote.timestamp)) / MINUTE;
  return Math.max(0, Math.round(age));
}

export function isStale(ageInMinutes: number): boolean {
  return ageInMinutes > STALE_AFTER_MINUTES;
}

export interface Market {
  fresh: Quote[];
  stale: Quote[];
  cheapestToBuy: Quote | null;
  bestToSell: Quote | null;
  medianSell: number | null;
}

function median(values: number[]): number | null {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  const upper = sorted[middle];
  const lower = sorted[middle - 1];
  if (upper === undefined) {
    return null;
  }
  return sorted.length % 2 === 1 || lower === undefined ? upper : (lower + upper) / 2;
}

/**
 * Where to buy a dollar cheapest is the lowest `sell`, and where to sell one for the
 * most is the highest `buy`. Ties go to the quote listed first.
 */
export function summarize(quotes: Quote[], generatedAt: string): Market {
  const fresh: Quote[] = [];
  const stale: Quote[] = [];
  for (const quote of quotes) {
    (isStale(ageMinutes(quote, generatedAt)) ? stale : fresh).push(quote);
  }

  let cheapestToBuy: Quote | null = null;
  let bestToSell: Quote | null = null;
  for (const quote of fresh) {
    if (cheapestToBuy === null || quote.sell < cheapestToBuy.sell) {
      cheapestToBuy = quote;
    }
    if (bestToSell === null || quote.buy > bestToSell.buy) {
      bestToSell = quote;
    }
  }

  return {
    fresh,
    stale,
    cheapestToBuy,
    bestToSell,
    medianSell: median(fresh.map((quote) => quote.sell)),
  };
}

/**
 * What to append to a claim that one price is the cheapest or the best. A source that
 * returned nothing is missing from the ranking, so the claim holds only for the houses
 * that answered.
 */
export function rankingScope(failures: Failure[]): string {
  return failures.length === 0 ? "" : " among the houses that answered";
}

/**
 * What to say beside the best prices when a source returned nothing. Its prices are
 * missing from the ranking, so the best price shown may not be the best price there is.
 */
export function missingSourcesNotice(failures: Failure[]): string | null {
  if (failures.length === 0) {
    return null;
  }
  const names = failures.map((failure) => failure.source).join(", ");
  const subject = failures.length === 1 ? "1 source" : `${failures.length} sources`;
  return `${subject} did not answer in this snapshot (${names}). Their prices are not counted, so a better price may exist.`;
}

export interface MarketPoint {
  t: number;
  lowestSell: number;
  highestBuy: number;
  houses: number;
}

/** The best price on each side at every snapshot, counting current quotes only. */
export function marketSeries(snapshots: Snapshot[]): MarketPoint[] {
  const points: MarketPoint[] = [];
  for (const snapshot of snapshots) {
    let lowestSell = Infinity;
    let highestBuy = -Infinity;
    let houses = 0;
    for (const price of Object.values(snapshot.prices)) {
      if (isStale(price.ageMinutes)) {
        continue;
      }
      lowestSell = Math.min(lowestSell, price.sell);
      highestBuy = Math.max(highestBuy, price.buy);
      houses += 1;
    }
    if (houses > 0) {
      points.push({ t: snapshot.t, lowestSell, highestBuy, houses });
    }
  }
  return points;
}

export interface HousePoint {
  t: number;
  buy: number;
  sell: number;
}

/** One quote's prices over time, leaving out the snapshots where it was missing or stale. */
export function houseSeries(snapshots: Snapshot[], id: string): HousePoint[] {
  const points: HousePoint[] = [];
  for (const snapshot of snapshots) {
    const price = snapshot.prices[id];
    if (price !== undefined && !isStale(price.ageMinutes)) {
      points.push({ t: snapshot.t, buy: price.buy, sell: price.sell });
    }
  }
  return points;
}
