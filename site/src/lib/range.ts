export const RANGES = ["24h", "7d", "30d", "all"] as const;
export type Range = (typeof RANGES)[number];

export const RANGE_LABELS: Record<Range, string> = {
  "24h": "24 hours",
  "7d": "7 days",
  "30d": "30 days",
  all: "All",
};

const HOUR = 3_600_000;
const SPAN: Record<Exclude<Range, "all">, number> = {
  "24h": 24 * HOUR,
  "7d": 7 * 24 * HOUR,
  "30d": 30 * 24 * HOUR,
};

/** Points up to `end` that fall inside the range, which counts back from `end`. */
export function sliceRange<T extends { t: number }>(
  points: T[],
  range: Range,
  end: number,
): T[] {
  if (range === "all") {
    return points;
  }
  const start = end - SPAN[range];
  return points.filter((point) => point.t >= start && point.t <= end);
}

/**
 * Cuts a series to about `maxPoints` by splitting its time span into equal buckets and
 * keeping the last point of each. The last point of the series always survives, so the
 * chart ends on the current price.
 */
export function downsample<T extends { t: number }>(points: T[], maxPoints: number): T[] {
  const first = points[0];
  const last = points.at(-1);
  if (first === undefined || last === undefined || points.length <= maxPoints) {
    return points;
  }
  const width = (last.t - first.t) / maxPoints;
  if (width === 0) {
    return [last];
  }

  const kept = new Map<number, T>();
  for (const point of points) {
    const bucket = Math.min(maxPoints - 1, Math.floor((point.t - first.t) / width));
    kept.set(bucket, point);
  }
  return [...kept.values()];
}
