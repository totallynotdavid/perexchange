import { buildChart } from "./chart.ts";
import type { Chart, ChartPoint } from "./chart.ts";
import { formatPrice } from "./format.ts";
import { HOUSE_RANGES, downsample, sliceRange } from "./range.ts";
import type { Range } from "./range.ts";

/** Enough points for a 30 day line at the widest chart. */
const MAX_POINTS = 240;

/** Readings further apart than this are not joined by a line. */
const MAX_GAP = 3 * 3_600_000;

/**
 * The page stretches a drawing to its frame, so these sizes set the proportions the
 * margins and tick spacing are planned for. The narrow one is for a phone, and the page
 * shows one of the two.
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

/** The move from the first reading in the range to the latest, signed. Empty with fewer than two readings. */
export function changeText(summary: SeriesSummary): string {
  const { first, latest } = summary;
  if (first === null || latest === null || summary.count < 2) {
    return "";
  }
  const change = Math.round((latest - first.v) * 10_000) / 10_000;
  if (change === 0) {
    return "No change";
  }
  const percent = (Math.abs(change) / first.v) * 100;
  const size = percent < 0.1 ? "<0.1%" : `${percent.toFixed(1)}%`;
  return `${change > 0 ? "+" : "−"}${formatPrice(Math.abs(change))} (${size})`;
}

/** A drawn point as the page script reads it: minutes since the epoch, and the price. */
export type Reading = [minute: number, value: number];

export interface RangeChart {
  range: Range;
  wide: Chart;
  narrow: Chart;
  summaries: SeriesSummary[];
  /** The drawn points of each series, so the page can read the line under the pointer. */
  readings: { id: string; points: Reading[] }[];
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
      readings: drawn.map((one) => ({
        id: one.id,
        points: one.points.map((point): Reading => [
          Math.round(point.t / 60_000),
          point.v,
        ]),
      })),
    };
  });
}
