import { rm } from "node:fs/promises";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { loadHistory, loadLatest } from "../src/lib/load.ts";
import {
  STALE_AFTER_MINUTES,
  houseSeries,
  marketSeries,
  summarize,
} from "../src/lib/market.ts";
import { recordSnapshots } from "./record.ts";
import { scratchDir } from "./scratch.ts";

let dir: string;

beforeEach(async () => {
  dir = await scratchDir("data");
  recordSnapshots(dir);
});

afterEach(async () => {
  await rm(dir, { recursive: true, force: true });
});

describe("data written by tools/snapshot.py", () => {
  it("loads as the newest fetch, with its failures", async () => {
    const latest = await loadLatest(dir);

    expect(latest.generated_at).toBe("2026-10-08T12:15:00Z");
    expect(latest.rates.map((rate) => rate.id)).toEqual(["cambiafx"]);
    expect(latest.failures).toEqual([
      {
        source: "cambiomundial",
        error_type: "HTTPStatusError",
        message: "403 Forbidden",
      },
    ]);
  });

  it("loads every fetch of the day as history", async () => {
    const { snapshots, skippedLines } = await loadHistory(dir);

    expect(skippedLines).toBe(0);
    expect(snapshots).toHaveLength(2);
    expect(Object.keys(snapshots[0].prices)).toEqual([
      "cambiafx",
      "gordito-digital",
      "chapacambio",
    ]);
  });

  it("gives the market a best price that ignores a house gone stale", async () => {
    const { snapshots } = await loadHistory(dir);
    const [first, second] = marketSeries(snapshots);

    expect(snapshots[0].prices.chapacambio.ageMinutes).toBeGreaterThan(
      STALE_AFTER_MINUTES,
    );
    expect(first.lowestSell).toBe(3.455);
    expect(first.houses).toBe(2);
    expect(second.lowestSell).toBe(3.45);
  });

  it("follows one house across fetches", async () => {
    const { snapshots } = await loadHistory(dir);

    expect(houseSeries(snapshots, "cambiafx").map((point) => point.sell)).toEqual([
      3.458, 3.45,
    ]);
  });

  it("summarizes the newest fetch", async () => {
    const latest = await loadLatest(dir);

    expect(summarize(latest.rates, latest.generated_at).cheapestToBuy?.sell).toBe(3.45);
  });
});

describe("loading an empty data directory", () => {
  it("names the command that records a snapshot", async () => {
    await expect(loadLatest(path.join(dir, "missing"))).rejects.toThrow(/bun run data/);
  });

  it("has no history", async () => {
    expect((await loadHistory(path.join(dir, "missing"))).snapshots).toEqual([]);
  });
});
