import { describe, expect, it } from "vitest";

import { describeChange, rangeCharts } from "../src/lib/chart-data.ts";
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

const moves = (from: number, to: number, days = 7): SeriesInput[] => [
  {
    id: "sell",
    label: "Lowest sell",
    kind: "sell",
    points: [
      { t: END - days * 24 * HOUR, v: from },
      { t: END, v: to },
    ],
  },
];

function change(from: number, to: number, range: "7d" | "all" = "7d"): string {
  const charts = rangeCharts(moves(from, to), END, ["7d", "all"]);
  const chart = charts.find((one) => one.range === range);
  return describeChange(chart!.summaries[0], range);
}

describe("rangeCharts", () => {
  it("draws every range twice, a wide chart and a narrow one, from the same points", () => {
    const [day] = rangeCharts(series(48), END);

    expect(day.range).toBe("24h");
    expect(day.wide.width).toBeGreaterThan(day.narrow.width);
    expect(day.wide.series[0].dots).toHaveLength(day.narrow.series[0].dots.length);
  });

  it("counts a range from the newest snapshot", () => {
    const charts = rangeCharts(series(48), END);
    const byRange = Object.fromEntries(charts.map((chart) => [chart.range, chart]));

    expect(byRange["24h"].summaries[0].count).toBe(25);
    expect(byRange["7d"].summaries[0].count).toBe(48);
  });

  it("takes the low and high from every snapshot, not from the drawn points", () => {
    const input = series(1000);
    input[0].points[500].v = 9;
    const month = rangeCharts(input, END).find((chart) => chart.range === "30d");

    expect(month?.summaries[0].high).toBe(9);
  });

  it("leaves a range with no snapshots empty", () => {
    const [day] = rangeCharts(series(1), END - 40 * 24 * HOUR);

    expect(day.summaries[0].count).toBe(0);
    expect(day.wide.series).toEqual([]);
  });
});

describe("describeChange", () => {
  it("says how far the price moved, in soles and in percent", () => {
    expect(change(3.451, 3.436)).toBe(
      "Down S/ 0.0150 (0.4%) in 7 days, from S/ 3.4510 to S/ 3.4360.",
    );
    expect(change(3.436, 3.45)).toBe(
      "Up S/ 0.0140 (0.4%) in 7 days, from S/ 3.4360 to S/ 3.4500.",
    );
  });

  it("says unchanged when the price did not move", () => {
    expect(change(3.436, 3.436)).toBe("Unchanged in 7 days, at S/ 3.4360.");
  });

  it("names the day the record starts when the range is all", () => {
    expect(change(3.451, 3.436, "all")).toContain("since 1 Oct");
  });

  it("says so when there is one reading and no line", () => {
    const [chart] = rangeCharts(
      [{ id: "sell", label: "x", kind: "sell", points: [{ t: END, v: 3.4 }] }],
      END,
      ["7d"],
    );

    expect(describeChange(chart.summaries[0], "7d")).toBe(
      "One reading so far, so there is no line yet.",
    );
  });
});
