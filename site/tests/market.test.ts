import { describe, expect, it } from "vitest";

import type { Failure } from "../src/lib/data.ts";
import {
  DEAD_AFTER_MINUTES,
  ageMinutes,
  bestSeries,
  gapToBest,
  houseSeries,
  missingHouses,
  missingSince,
  placeOf,
  rank,
} from "../src/lib/market.ts";
import { GENERATED_AT, quote, snapshot } from "./fixtures.ts";

const minutesBefore = (minutes: number) =>
  new Date(Date.parse(GENERATED_AT) - minutes * 60_000).toISOString();

const failure = (source: string, reason: Failure["reason"] = "blocked"): Failure => ({
  source,
  reason,
  message: "",
});

describe("rank", () => {
  const quotes = [quote("a", 3.3, 3.5), quote("b", 3.4, 3.45), quote("c", 3.2, 3.6)];

  it("puts the lowest price first for someone buying dollars", () => {
    expect(rank(quotes, "buy", GENERATED_AT).map((q) => q.id)).toEqual(["b", "a", "c"]);
  });

  it("puts the highest price first for someone selling dollars", () => {
    expect(rank(quotes, "sell", GENERATED_AT).map((q) => q.id)).toEqual(["b", "a", "c"]);
  });

  it("puts the newer of two equal rates first", () => {
    const older = quote("older", 3.3, 3.4, minutesBefore(40));
    const newer = quote("newer", 3.3, 3.4, minutesBefore(5));

    expect(rank([older, newer], "buy", GENERATED_AT).map((q) => q.id)).toEqual([
      "newer",
      "older",
    ]);
  });

  it("leaves out a rate its house has not changed in a day", () => {
    const closed = quote("closed", 3.9, 3.0, minutesBefore(DEAD_AFTER_MINUTES + 1));
    const edge = quote("edge", 3.3, 3.4, minutesBefore(DEAD_AFTER_MINUTES));

    expect(rank([closed, edge], "buy", GENERATED_AT).map((q) => q.id)).toEqual(["edge"]);
  });

  it("ranks a house's own rate and not its special rates", () => {
    const own = quote("tkambio", 3.4, 3.46);
    const large = { ...quote("tkambio-5000", 3.43, 3.44), source: "tkambio" };

    expect(rank([own, large], "buy", GENERATED_AT).map((q) => q.id)).toEqual(["tkambio"]);
  });

  it("has nothing to rank without current quotes", () => {
    expect(rank([], "buy", GENERATED_AT)).toEqual([]);
  });
});

describe("gapToBest and placeOf", () => {
  const quotes = [quote("a", 3.3, 3.5), quote("b", 3.4, 3.45), quote("c", 3.4, 3.45)];
  const [a, b, c] = quotes;

  it("measures how far a rate is from the best on the side that matters", () => {
    expect(gapToBest(a, b, "buy")).toBe(0.05);
    expect(gapToBest(a, b, "sell")).toBe(0.1);
    expect(gapToBest(b, b, "buy")).toBe(0);
  });

  it("gives houses that tie for the best the same place", () => {
    expect(placeOf(quotes, b, "buy", GENERATED_AT)).toEqual({ place: 1, of: 3, gap: 0 });
    expect(placeOf(quotes, c, "buy", GENERATED_AT)).toEqual({ place: 1, of: 3, gap: 0 });
    expect(placeOf(quotes, a, "buy", GENERATED_AT)).toEqual({
      place: 3,
      of: 3,
      gap: 0.05,
    });
  });

  it("does not place a rate that is not ranked", () => {
    const old = quote("old", 3.4, 3.4, minutesBefore(DEAD_AFTER_MINUTES + 1));

    expect(placeOf([a, old], old, "buy", GENERATED_AT)).toBeNull();
  });
});

describe("ageMinutes", () => {
  it("is the whole minutes between the snapshot and the quote, never negative", () => {
    expect(ageMinutes(quote("a", 1, 1, minutesBefore(154)), GENERATED_AT)).toBe(154);
    expect(ageMinutes(quote("a", 1, 1, minutesBefore(-3)), GENERATED_AT)).toBe(0);
  });
});

describe("missingSince", () => {
  const down = (minutes: number) => snapshot(minutes, { a: [3.4, 3.45] }, ["x"]);
  const up = (minutes: number) => snapshot(minutes, { a: [3.4, 3.45] }, []);

  it("dates the start of the run of fetches the source has been missing from", () => {
    const found = missingSince([up(0), down(15), down(30)], "x");

    expect(found).toEqual({ at: down(15).t, atLeast: false });
  });

  it("says at least when the history ends before the source last answered", () => {
    expect(missingSince([down(0), down(15)], "x")).toEqual({
      at: down(0).t,
      atLeast: true,
    });
  });

  it("does not guess from fetches recorded without the list", () => {
    const unknown = snapshot(0, { a: [3.4, 3.45] });

    expect(missingSince([unknown, down(15)], "x")).toEqual({
      at: down(15).t,
      atLeast: true,
    });
    expect(missingSince([unknown], "x")).toBeNull();
  });

  it("is null for a source that answered in the newest fetch", () => {
    expect(missingSince([down(0), up(15)], "x")).toBeNull();
  });
});

describe("missingHouses", () => {
  const history = [
    snapshot(0, { a: [3.4, 3.45] }, []),
    snapshot(15, { a: [3.4, 3.45] }, ["blocked"]),
  ];

  it("names a house that returned nothing, why, and since when", () => {
    const [house] = missingHouses(
      [quote("a", 3.4, 3.45)],
      [failure("blocked")],
      history,
      GENERATED_AT,
    );

    expect(house.name).toBe("blocked");
    expect(house.why).toBe("Blocks requests from our server since 7 Oct.");
  });

  it("does not list a house another listing still covers", () => {
    const aggregator = {
      ...quote("cuantoestaeldolar", 3.4, 3.45),
      name: "Cambio Mundial",
    };

    expect(
      missingHouses([aggregator], [failure("cambiomundial")], history, GENERATED_AT),
    ).toEqual([]);
  });

  it("lists a house whose only rate is too old, with the day it last changed", () => {
    const old = {
      ...quote("mercadocambiario", 3.4, 3.45, "2025-06-10T12:00:00Z"),
      name: "Mercado Cambiario",
    };

    expect(missingHouses([old], [], [], GENERATED_AT)).toEqual([
      { name: "Mercado Cambiario", why: "Has not changed its rate since 10 Jun." },
    ]);
  });

  it("lists nothing when every house has a current rate", () => {
    expect(missingHouses([quote("a", 3.4, 3.45)], [], history, GENERATED_AT)).toEqual([]);
  });
});

describe("houseSeries", () => {
  it("returns one quote's prices where it was present and current", () => {
    const points = houseSeries(
      [
        snapshot(0, { a: [3.4, 3.46] }),
        snapshot(15, { b: [3.4, 3.46] }),
        snapshot(30, { a: [3.41, 3.47, DEAD_AFTER_MINUTES + 1] }),
        snapshot(45, { a: [3.42, 3.48] }),
      ],
      "a",
    );

    expect(points.map((p) => p.sell)).toEqual([3.46, 3.48]);
  });
});

describe("bestSeries", () => {
  const snapshots = [
    snapshot(0, { a: [3.4, 3.46], b: [3.41, 3.45], "b-5000": [3.3, 3.2] }),
    snapshot(15, { a: [3.42, 3.47], b: [3.41, 3.45, DEAD_AFTER_MINUTES + 1] }),
    snapshot(30, { b: [3.4, 3.5, DEAD_AFTER_MINUTES + 1] }),
    snapshot(45, { a: [3.43, 3.44] }),
  ];
  const variants = new Set(["a", "b"]);

  it("leaves out a special rate that only older history holds", () => {
    const older = [
      snapshot(0, {
        a: [3.4, 3.46],
        "a-5000": [3.3, 3.2],
        gone: [3.4, 3.47],
        "gone-big": [3.3, 3.1],
      }),
    ];

    expect(bestSeries(older, "buy", variants).map((p) => p.v)).toEqual([3.46]);
    expect(bestSeries(older, "sell", variants).map((p) => p.v)).toEqual([3.4]);
  });

  it("keeps a house whose id has a hyphen but is nobody's special rate", () => {
    const hyphen = [snapshot(0, { "cambio-mundial": [3.43, 3.44], a: [3.4, 3.46] })];

    expect(bestSeries(hyphen, "buy", variants).map((p) => p.v)).toEqual([3.44]);
  });

  it("takes the lowest sell rate for someone buying, without special rates", () => {
    expect(bestSeries(snapshots, "buy", variants).map((p) => p.v)).toEqual([
      3.45, 3.47, 3.44,
    ]);
  });

  it("takes the highest buy rate for someone selling, without special rates", () => {
    expect(bestSeries(snapshots, "sell", variants).map((p) => p.v)).toEqual([
      3.41, 3.42, 3.43,
    ]);
  });

  it("leaves out a snapshot in which no house has a current rate", () => {
    const times = bestSeries(snapshots, "buy", variants).map((p) => p.t);

    expect(times).toHaveLength(3);
    expect(times).not.toContain(snapshots[2]?.t);
  });
});
