import { describe, expect, it } from "vitest";

import { rangeCharts } from "../src/lib/chart-data.ts";
import type { SeriesInput } from "../src/lib/chart-data.ts";

const HOUR = 3_600_000;
const END = Date.parse("2026-10-08T12:00:00Z");

function series(hours: number): SeriesInput[] {
  const points = Array.from({ length: hours }, (_, i) => ({
    t: END - (hours - 1 - i) * HOUR,
    v: 3.4 + (i % 7) * 0.01,
  }));
  return [{ id: "sell", label: "Lowest sell", kind: "sell", points }];
}

describe("rangeCharts", () => {
  it("draws every range twice, a wide chart and a narrow one, from the same points", () => {
    const [day] = rangeCharts(series(48), END);

    expect(day.range).toBe("24h");
    expect(day.wide.width).toBeGreaterThan(day.narrow.width);
    expect(day.wide.xTicks.length).toBeGreaterThan(day.narrow.xTicks.length);
    expect(day.wide.series[0].dots).toHaveLength(day.narrow.series[0].dots.length);
  });

  it("counts a range from the newest snapshot", () => {
    const charts = rangeCharts(series(48), END);
    const byRange = Object.fromEntries(charts.map((chart) => [chart.range, chart]));

    expect(byRange["24h"].snapshots).toBe(25);
    expect(byRange["7d"].snapshots).toBe(48);
  });

  it("takes the low and high from every snapshot, not from the drawn points", () => {
    const input = series(1000);
    input[0].points[500].v = 9;
    const all = rangeCharts(input, END).find((chart) => chart.range === "all");

    expect(all?.summaries[0].high).toBe(9);
  });

  it("leaves a range with no snapshots empty", () => {
    const [day] = rangeCharts(series(1), END - 40 * 24 * HOUR);

    expect(day.snapshots).toBe(0);
    expect(day.wide.series).toEqual([]);
  });
});
