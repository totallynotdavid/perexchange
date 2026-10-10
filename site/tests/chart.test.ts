import { describe, expect, it } from "vitest";

import { buildChart, priceAxis } from "../src/lib/chart.ts";

const HOUR = 3_600_000;
const DAY = 24 * HOUR;
// Midnight in Lima, which keeps UTC-5 all year.
const START = Date.parse("2026-10-08T05:00:00Z");

describe("priceAxis", () => {
  it("puts round numbers on the axis around the data", () => {
    const axis = priceAxis(3.44, 3.49);

    expect(axis.min).toBeLessThan(3.44);
    expect(axis.max).toBeGreaterThan(3.49);
    expect(axis.ticks.length).toBeGreaterThanOrEqual(2);
    expect(axis.ticks.length).toBeLessThanOrEqual(7);
    for (const tick of axis.ticks) {
      expect(tick).toBeGreaterThanOrEqual(axis.min);
      expect(tick).toBeLessThanOrEqual(axis.max);
    }
  });

  it("never stretches a move of a cent or two to the height of the chart", () => {
    const axis = priceAxis(3.435, 3.455);

    expect((3.455 - 3.435) / (axis.max - axis.min)).toBeLessThan(0.2);
  });

  it("opens up a flat series so the line sits in the middle", () => {
    const axis = priceAxis(3.45, 3.45);

    expect(axis.max - axis.min).toBeGreaterThan(0.1);
    expect((axis.max + axis.min) / 2).toBeCloseTo(3.45, 6);
  });
});

describe("buildChart", () => {
  const series = [
    {
      id: "sell",
      label: "Lowest sell",
      points: [0, 1, 2].map((i) => ({ t: START + i * HOUR, v: 3.44 + i * 0.01 })),
    },
  ];

  it("draws a rising price higher on the page and later to the right", () => {
    const chart = buildChart(series, 640, 240);
    const [first, , last] = chart.series[0].dots;

    expect(last.x).toBeGreaterThan(first.x);
    expect(last.y).toBeLessThan(first.y);
    expect(chart.series[0].last.value).toBe(3.46);
  });

  it("keeps every point inside the plot area", () => {
    const { plot, series: drawn } = buildChart(series, 640, 240);

    for (const dot of drawn[0].dots) {
      expect(dot.x).toBeGreaterThanOrEqual(plot.left);
      expect(dot.x).toBeLessThanOrEqual(plot.right);
      expect(dot.y).toBeGreaterThanOrEqual(plot.top);
      expect(dot.y).toBeLessThanOrEqual(plot.bottom);
    }
  });

  const over = (days: number) => [
    {
      id: "s",
      label: "s",
      // The readings never fall on a day boundary, as real runs do not.
      points: [
        { t: START + 22 * 60_000 + 37_000, v: 3.4 },
        { t: START + days * DAY + 41 * 60_000, v: 3.5 },
      ],
    },
  ];

  it("labels a week with whole days, never a time of day", () => {
    const labels = buildChart(over(7), 760, 280, 8).xTicks.map((tick) => tick.label);

    expect(labels).toEqual([
      "9 Oct",
      "10 Oct",
      "11 Oct",
      "12 Oct",
      "13 Oct",
      "14 Oct",
      "15 Oct",
    ]);
  });

  it("thins the day labels for a narrow chart and a long range, without a time of day", () => {
    const narrow = buildChart(over(7), 330, 250, 4).xTicks.map((tick) => tick.label);
    const year = buildChart(over(300), 760, 280, 8).xTicks;

    expect(narrow).toEqual(["9 Oct", "11 Oct", "13 Oct", "15 Oct"]);
    expect(year.length).toBeLessThanOrEqual(8);
    expect(year.every((tick) => /^\d+ \w{3}$/.test(tick.label))).toBe(true);
  });

  it("labels a day with whole hours", () => {
    const day = buildChart(
      [
        {
          id: "s",
          label: "s",
          points: [
            { t: START + 22 * 60_000, v: 3.4 },
            { t: START + 20 * HOUR + 7 * 60_000, v: 3.5 },
          ],
        },
      ],
      760,
      280,
      5,
    );

    expect(day.xTicks.map((tick) => tick.label)).toEqual([
      "04:00",
      "08:00",
      "12:00",
      "16:00",
      "20:00",
    ]);
  });

  it("writes the labels at the plot's edges inward, so none is cut off", () => {
    const { xTicks } = buildChart(over(7), 760, 280, 8);

    expect(xTicks[0].anchor).not.toBe("end");
    expect(xTicks.at(-1)?.anchor).not.toBe("start");
    expect(xTicks.some((tick) => tick.anchor === "middle")).toBe(true);
  });

  it("draws a single point as a dot in the middle", () => {
    const chart = buildChart(
      [{ id: "s", label: "s", points: [{ t: START, v: 3.45 }] }],
      640,
      240,
    );

    expect(chart.series[0].dots).toHaveLength(1);
    expect(chart.series[0].dots[0].x).toBe((chart.plot.left + chart.plot.right) / 2);
    expect(chart.xTicks).toHaveLength(1);
  });

  it("returns an empty chart when no series has points", () => {
    expect(buildChart([{ id: "s", label: "s", points: [] }], 640, 240).series).toEqual(
      [],
    );
  });
});
