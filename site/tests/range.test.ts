import { describe, expect, it } from "vitest";

import { downsample, sliceRange } from "../src/lib/range.ts";

const HOUR = 3_600_000;
const END = Date.parse("2026-10-08T12:00:00Z");
const hoursAgo = (h: number) => ({ t: END - h * HOUR });

describe("sliceRange", () => {
  const points = [hoursAgo(100), hoursAgo(30), hoursAgo(5), hoursAgo(0)];

  it("keeps the points inside the window that ends at the newest snapshot", () => {
    expect(sliceRange(points, "24h", END)).toEqual([hoursAgo(5), hoursAgo(0)]);
    expect(sliceRange(points, "7d", END)).toHaveLength(4);
  });
});

describe("downsample", () => {
  const series = Array.from({ length: 1000 }, (_, i) => ({ t: i * 60_000, v: i }));

  it("returns a short series unchanged", () => {
    expect(downsample(series.slice(0, 10), 50)).toHaveLength(10);
  });

  it("cuts a long series to at most the limit and ends on the newest point", () => {
    const cut = downsample(series, 100);

    expect(cut.length).toBeLessThanOrEqual(100);
    expect(cut.length).toBeGreaterThan(90);
    expect(cut[cut.length - 1]).toBe(series[999]);
  });

  it("keeps the order of time", () => {
    const times = downsample(series, 100).map((p) => p.t);

    expect(times).toEqual([...times].sort((a, b) => a - b));
  });

  it("collapses points that share one instant", () => {
    const same = [{ t: 5 }, { t: 5 }, { t: 5 }];

    expect(downsample(same, 2)).toEqual([{ t: 5 }]);
  });
});
