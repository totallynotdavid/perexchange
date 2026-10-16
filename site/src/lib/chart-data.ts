import { buildChart } from "./chart.ts";
import type { Chart, ChartPoint } from "./chart.ts";
import { formatDay, formatPrice } from "./format.ts";
import { HOUSE_RANGES, RANGE_LABELS, downsample, sliceRange } from "./range.ts";
import type { Range } from "./range.ts";

/** Enough points for a 30 day line at the widest chart. */
const MAX_POINTS = 240;

/** Readings further apart than this are not joined by a line. */
const MAX_GAP = 3 * 3_600_000;

/**
 * Each chart is drawn at close to the size it is shown, so its text stays readable.
 * The narrow one is for a phone, and the page shows one of the two.
 */
const SIZES = {
  wide: { width: 760, height: 280, xTicks: 8 },
  narrow: { width: 330, height: 250, xTicks: 4 },
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
  /** The time and value of the oldest point in the range. */
  first: ChartPoint | null;
  latest: number | null;
  low: number | null;
  high: number | null;
}

export function describeChange(summary: SeriesSummary, range: Range): string {
  const { first, latest } = summary;
  if (first === null || latest === null || summary.count === 0) {
    return "";
  }
  if (summary.count === 1) {
    return "One reading so far, so there is no line yet.";
  }
  const span =
    range === "all"
      ? `since ${formatDay(first.t)}`
      : `in ${RANGE_LABELS[range].toLowerCase()}`;
  const change = Math.round((latest - first.v) * 10_000) / 10_000;
  if (change === 0) {
    return `Unchanged ${span}, at S/ ${formatPrice(latest)}.`;
  }
  const percent = (Math.abs(change) / first.v) * 100;
  const size = percent < 0.1 ? "under 0.1%" : `${percent.toFixed(1)}%`;
  return `${change > 0 ? "Up" : "Down"} S/ ${formatPrice(Math.abs(change))} (${size}) ${span}, from S/ ${formatPrice(first.v)} to S/ ${formatPrice(latest)}.`;
}

export interface RangeChart {
  range: Range;
  wide: Chart;
  narrow: Chart;
  summaries: SeriesSummary[];
}

function summarize(series: SeriesInput): SeriesSummary {
  const values = series.points.map((point) => point.v);
  return {
    id: series.id,
    label: series.label,
    count: values.length,
    first: series.points[0] ?? null,
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
export function rangeCharts(
  series: SeriesInput[],
  end: number,
  ranges: readonly Range[] = HOUSE_RANGES,
): RangeChart[] {
  return ranges.map((range) => {
    const inRange = series.map((one) => ({
      ...one,
      points: sliceRange(one.points, range, end),
    }));
    const drawn = inRange.map((one) => ({
      ...one,
      points: downsample(one.points, MAX_POINTS),
    }));
    // Downsampling spaces points up to two buckets apart, so a longer range tolerates more.
    const span = Math.max(
      0,
      ...inRange.map(
        (one) => (one.points.at(-1)?.t ?? 0) - (one.points[0]?.t ?? 0),
      ),
    );
    const maxGap = Math.max(MAX_GAP, (2 * span) / MAX_POINTS);
    const draw = (size: (typeof SIZES)[keyof typeof SIZES]) =>
      buildChart(drawn, size.width, size.height, size.xTicks, maxGap);
    return {
      range,
      wide: draw(SIZES.wide),
      narrow: draw(SIZES.narrow),
      summaries: inRange.map(summarize),
    };
  });
}
