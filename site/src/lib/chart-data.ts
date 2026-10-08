import { buildChart } from "./chart.ts";
import type { Chart, ChartPoint } from "./chart.ts";
import { RANGES, downsample, sliceRange } from "./range.ts";
import type { Range } from "./range.ts";

/** Enough points for a 30 day line at the widest chart. */
const MAX_POINTS = 240;

/**
 * Each chart is drawn at close to the size it is shown, so its text stays readable.
 * The narrow one is for a phone, and the page shows one of the two.
 */
const SIZES = {
  wide: { width: 760, height: 280, xTicks: 5 },
  narrow: { width: 330, height: 250, xTicks: 3 },
} as const;

export interface SeriesInput {
  id: string;
  label: string;
  /** The CSS class that gives the line its color and dash. */
  kind: "sell" | "buy";
  points: ChartPoint[];
}

export interface SeriesSummary {
  id: string;
  label: string;
  count: number;
  latest: number | null;
  low: number | null;
  high: number | null;
}

export interface RangeChart {
  range: Range;
  wide: Chart;
  narrow: Chart;
  summaries: SeriesSummary[];
  /** The number of snapshots behind the longest series. */
  snapshots: number;
}

function summarize(series: SeriesInput): SeriesSummary {
  const values = series.points.map((point) => point.v);
  return {
    id: series.id,
    label: series.label,
    count: values.length,
    latest: values.at(-1) ?? null,
    low: values.length === 0 ? null : Math.min(...values),
    high: values.length === 0 ? null : Math.max(...values),
  };
}

/**
 * Charts for every range, each counting back from `end`, the newest snapshot. The
 * summaries come from the full-resolution points, so a low or high is never smoothed
 * away by downsampling.
 */
export function rangeCharts(series: SeriesInput[], end: number): RangeChart[] {
  return RANGES.map((range) => {
    const inRange = series.map((one) => ({
      ...one,
      points: sliceRange(one.points, range, end),
    }));
    const drawn = inRange.map((one) => ({
      ...one,
      points: downsample(one.points, MAX_POINTS),
    }));
    const draw = (size: (typeof SIZES)[keyof typeof SIZES]) =>
      buildChart(drawn, size.width, size.height, size.xTicks);
    return {
      range,
      wide: draw(SIZES.wide),
      narrow: draw(SIZES.narrow),
      summaries: inRange.map(summarize),
      snapshots: Math.max(0, ...inRange.map((one) => one.points.length)),
    };
  });
}
