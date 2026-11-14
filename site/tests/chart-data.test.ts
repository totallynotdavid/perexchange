import { describe, expect, it } from "vitest";

import { changeText, rangeCharts } from "../src/lib/chart-data.ts";
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

function change(from: number, to: number): string {
  const [chart] = rangeCharts(moves(from, to), END, ["7d"]);
  return changeText(chart.summaries[0]);
}

describe("rangeCharts", () => {
  it("draws every range twice, a wide chart and a narrow one, from the same points", () => {
    const [day] = rangeCharts(series(48), END);

    expect(day.range).toBe("24h");
    expect(day.wide.width).toBeGreaterThan(day.narrow.width);
    expect(day.wide.series[0].dots).toHaveLength(
      day.narrow.series[0].dots.length,
    );
  });

  it("counts a range from the newest snapshot", () => {
    const charts = rangeCharts(series(48), END);
    const byRange = Object.fromEntries(
      charts.map((chart) => [chart.range, chart]),
    );

    expect(byRange["24h"].summaries[0].count).toBe(25);
    expect(byRange["7d"].summaries[0].count).toBe(48);
  });

  it("takes the low and high from every snapshot, not from the drawn points", () => {
    const input = series(1000);
    input[0].points[500].v = 9;
    const month = rangeCharts(input, END).find(
      (chart) => chart.range === "30d",
    );

    expect(month?.summaries[0].high).toBe(9);
  });

  it("lifts the line over a missing stretch but not over a downsampled one", () => {
    const hole = series(100).map((one) => ({
      ...one,
      points: one.points.filter((_, i) => i < 40 || i >= 50),
    }));
    const [day, week] = rangeCharts(hole, END, ["7d", "30d"]);
    const continuous = rangeCharts(series(1000), END, ["30d"])[0];

    expect(day.wide.series[0].path.match(/M/g)).toHaveLength(2);
    expect(week.wide.series[0].path.match(/M/g)).toHaveLength(2);
    expect(continuous.wide.series[0].path.match(/M/g)).toHaveLength(1);
  });

  it("leaves a range with no snapshots empty", () => {
    const [day] = rangeCharts(series(1), END - 40 * 24 * HOUR);

    expect(day.summaries[0].count).toBe(0);
    expect(day.wide.series).toEqual([]);
  });
});

describe("changeText", () => {
  it("signs the move over the range, in soles and in percent", () => {
    expect(change(3.451, 3.436)).toBe("−0.0150 (0.4%)");
    expect(change(3.436, 3.45)).toBe("+0.0140 (0.4%)");
  });

  it("marks a move under a tenth of a percent as such", () => {
    expect(change(3.436, 3.437)).toBe("+0.0010 (<0.1%)");
  });

  it("says no change when the price did not move", () => {
    expect(change(3.436, 3.436)).toBe("No change");
  });

  it("is empty with one reading, since nothing moved yet", () => {
    const [chart] = rangeCharts(
      [{ id: "sell", label: "x", kind: "sell", points: [{ t: END, v: 3.4 }] }],
      END,
      ["7d"],
    );

    expect(changeText(chart.summaries[0])).toBe("");
  });
});
