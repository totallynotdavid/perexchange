import { describe, expect, it } from "vitest";

import { buildChart, priceAxis } from "../src/lib/chart.ts";

const HOUR = 3_600_000;
const START = Date.parse("2026-10-08T00:00:00Z");

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

  it("opens up a flat series so the line sits in the middle", () => {
    const axis = priceAxis(3.45, 3.45);

    expect(axis.max - axis.min).toBeGreaterThan(0.015);
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

  it("labels the time axis with as many ticks as asked for, ends included", () => {
    const five = buildChart(series, 640, 240);
    const three = buildChart(series, 330, 250, 3);

    expect(five.xTicks).toHaveLength(5);
    expect(three.xTicks).toHaveLength(3);
    expect(three.xTicks[0].x).toBe(three.plot.left);
    expect(three.xTicks[2].x).toBe(three.plot.right);
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

  it("labels a short span with Lima clock times and a long one with dates", () => {
    const day = buildChart(series, 640, 240);
    const month = buildChart(
      [
        {
          id: "s",
          label: "s",
          points: [
            { t: START, v: 3.4 },
            { t: START + 30 * 24 * HOUR, v: 3.5 },
          ],
        },
      ],
      640,
      240,
    );

    expect(day.xTicks[0].label).toBe("19:00");
    expect(month.xTicks[0].label).toBe("7 Oct");
  });

  it("draws a single point as a dot in the middle", () => {
    const chart = buildChart(
      [{ id: "s", label: "s", points: [{ t: START, v: 3.45 }] }],
      640,
      240,
    );

    expect(chart.series[0].dots).toHaveLength(1);
    expect(chart.series[0].dots[0].x).toBe((chart.plot.left + chart.plot.right) / 2);
  });

  it("returns an empty chart when no series has points", () => {
    expect(buildChart([{ id: "s", label: "s", points: [] }], 640, 240).series).toEqual(
      [],
    );
  });
});
