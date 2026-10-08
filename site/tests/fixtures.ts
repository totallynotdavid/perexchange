import type { Quote, Snapshot } from "../src/lib/data.ts";

export const GENERATED_AT = "2026-10-08T14:30:00Z";

export function quote(
  id: string,
  buy: number,
  sell: number,
  timestamp = GENERATED_AT,
): Quote {
  return { id, source: id, name: id, buy, sell, timestamp };
}

export function snapshot(
  minutesAfterStart: number,
  prices: Record<string, [buy: number, sell: number, ageMinutes?: number]>,
): Snapshot {
  const start = Date.parse("2026-10-08T00:00:00Z");
  return {
    t: start + minutesAfterStart * 60_000,
    prices: Object.fromEntries(
      Object.entries(prices).map(([id, [buy, sell, ageMinutes = 0]]) => [
        id,
        { buy, sell, ageMinutes },
      ]),
    ),
  };
}
