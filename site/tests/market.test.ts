import { describe, expect, it } from "vitest";

import {
  STALE_AFTER_MINUTES,
  ageMinutes,
  houseSeries,
  marketSeries,
  missingSourcesNotice,
  rankingScope,
  summarize,
} from "../src/lib/market.ts";
import { GENERATED_AT, quote, snapshot } from "./fixtures.ts";

const minutesBefore = (minutes: number) =>
  new Date(Date.parse(GENERATED_AT) - minutes * 60_000).toISOString();

describe("rankingScope", () => {
  it("adds nothing when every source answered", () => {
    expect(rankingScope([])).toBe("");
  });

  it("limits a claim to the houses that answered when any source did not", () => {
    const failure = {
      source: "a",
      error_type: "HTTPStatusError",
      message: "403 Forbidden",
    };

    expect(rankingScope([failure])).toBe(" among the houses that answered");
  });
});

describe("missingSourcesNotice", () => {
  const failure = (source: string) => ({
    source,
    error_type: "HTTPStatusError",
    message: "403 Forbidden",
  });

  it("says nothing when every source answered", () => {
    expect(missingSourcesNotice([])).toBeNull();
  });

  it("names each source that did not answer and warns the best price may be missing", () => {
    expect(missingSourcesNotice([failure("a")])).toBe(
      "1 source did not answer in this snapshot (a). Their prices are not counted, so a better price may exist.",
    );
    expect(missingSourcesNotice([failure("a"), failure("b")])).toContain(
      "2 sources did not answer in this snapshot (a, b).",
    );
  });
});

describe("summarize", () => {
  it("picks the lowest sell price to buy and the highest buy price to sell", () => {
    const market = summarize(
      [quote("a", 3.3, 3.5), quote("b", 3.4, 3.45), quote("c", 3.2, 3.6)],
      GENERATED_AT,
    );

    expect(market.cheapestToBuy?.id).toBe("b");
    expect(market.bestToSell?.id).toBe("b");
    expect(market.medianSell).toBe(3.5);
  });

  it("never ranks a quote its house stopped updating", () => {
    const old = quote("old", 3.5, 3.3, minutesBefore(STALE_AFTER_MINUTES + 1));
    const market = summarize([old, quote("b", 3.4, 3.45)], GENERATED_AT);

    expect(market.cheapestToBuy?.id).toBe("b");
    expect(market.bestToSell?.id).toBe("b");
    expect(market.stale.map((q) => q.id)).toEqual(["old"]);
  });

  it("ranks a quote exactly at the limit", () => {
    const edge = quote("edge", 3.4, 3.3, minutesBefore(STALE_AFTER_MINUTES));

    expect(summarize([edge], GENERATED_AT).cheapestToBuy?.id).toBe("edge");
  });

  it("has nothing to rank when every quote is stale or none exist", () => {
    const old = quote("old", 3.4, 3.45, minutesBefore(600));

    expect(summarize([old], GENERATED_AT).cheapestToBuy).toBeNull();
    expect(summarize([], GENERATED_AT).medianSell).toBeNull();
  });

  it("averages the middle two sell prices of an even count", () => {
    const market = summarize([quote("a", 3.3, 3.4), quote("b", 3.3, 3.5)], GENERATED_AT);

    expect(market.medianSell).toBeCloseTo(3.45, 10);
  });
});

describe("ageMinutes", () => {
  it("is the whole minutes between the snapshot and the quote, never negative", () => {
    expect(ageMinutes(quote("a", 1, 1, minutesBefore(154)), GENERATED_AT)).toBe(154);
    expect(ageMinutes(quote("a", 1, 1, minutesBefore(-3)), GENERATED_AT)).toBe(0);
  });
});

describe("marketSeries", () => {
  it("follows the best price on each side over time", () => {
    const points = marketSeries([
      snapshot(0, { a: [3.4, 3.46], b: [3.42, 3.47] }),
      snapshot(15, { a: [3.41, 3.44], b: [3.39, 3.47] }),
    ]);

    expect(points.map((p) => [p.lowestSell, p.highestBuy, p.houses])).toEqual([
      [3.46, 3.42, 2],
      [3.44, 3.41, 2],
    ]);
  });

  it("leaves a stale quote out of the best price", () => {
    const [point] = marketSeries([
      snapshot(0, { a: [3.4, 3.46], old: [3.6, 3.3, STALE_AFTER_MINUTES + 1] }),
    ]);

    expect(point.lowestSell).toBe(3.46);
    expect(point.highestBuy).toBe(3.4);
    expect(point.houses).toBe(1);
  });

  it("skips a snapshot where nothing was current", () => {
    expect(marketSeries([snapshot(0, { old: [3.4, 3.46, 999] })])).toEqual([]);
  });
});

describe("houseSeries", () => {
  it("returns one quote's prices where it was present and current", () => {
    const points = houseSeries(
      [
        snapshot(0, { a: [3.4, 3.46] }),
        snapshot(15, { b: [3.4, 3.46] }),
        snapshot(30, { a: [3.41, 3.47, 400] }),
        snapshot(45, { a: [3.42, 3.48] }),
      ],
      "a",
    );

    expect(points.map((p) => p.sell)).toEqual([3.46, 3.48]);
  });
});
