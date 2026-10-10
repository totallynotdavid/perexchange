export interface ChartPoint {
  t: number;
  v: number;
}

export interface ChartSeries {
  id: string;
  label: string;
  points: ChartPoint[];
}

export interface DrawnSeries {
  id: string;
  label: string;
  path: string;
  /** Every point as a dot, so a series of one or two points is still visible. */
  dots: { x: number; y: number }[];
  last: { x: number; y: number; value: number };
}

export interface Chart {
  width: number;
  height: number;
  plot: { left: number; top: number; right: number; bottom: number };
  series: DrawnSeries[];
  yTicks: { y: number; label: string }[];
  xTicks: { x: number; label: string; anchor: "start" | "middle" | "end" }[];
}

const MARGIN = { left: 54, top: 10, right: 14, bottom: 26 };
const PRICE_STEPS = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1];
const MAX_Y_TICKS = 6;
const HOUR = 3_600_000;
const DAY = 24 * HOUR;
/** Lima keeps UTC-5 all year, so its midnight is a fixed offset from UTC. */
const LIMA_OFFSET = -5 * HOUR;
/** A tick this close to the plot's edge is written inward from it, so the label stays inside. */
const EDGE = 24;

/** The shortest span of price the axis shows, as a share of the price. */
const MIN_AXIS_SPAN = 0.04;

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

function niceStep(span: number): number {
  return PRICE_STEPS.find((step) => span / step <= MAX_Y_TICKS) ?? 1;
}

/**
 * The price axis: tick values that land on round numbers around the data. The axis spans
 * at least 4% of the price, so a move of a cent or two reads as the small move it is and
 * never as a spike.
 */
export function priceAxis(
  low: number,
  high: number,
): { min: number; max: number; ticks: number[] } {
  const mid = (low + high) / 2;
  const span = Math.max((high - low) * 1.24, mid * MIN_AXIS_SPAN);
  const min = mid - span / 2;
  const max = mid + span / 2;
  const step = niceStep(span);

  const ticks: number[] = [];
  for (let tick = Math.ceil(min / step) * step; tick <= max + 1e-9; tick += step) {
    ticks.push(Number(tick.toFixed(4)));
  }
  return { min, max, ticks };
}

const HOUR_STEPS = [1, 2, 3, 4, 6, 12];
const DAY_STEPS = [1, 2, 3, 7, 14, 30, 60, 90, 180];

/**
 * Moments to label: whole hours when the chart covers a day or so, whole Lima days when it
 * covers more. The step is the smallest that leaves no more than `max` labels, so no tick
 * claims a precision the readings do not have.
 */
function timeTicks(
  start: number,
  end: number,
  max: number,
): { t: number; label: string }[] {
  const days = end - start > 1.5 * DAY;
  const unit = days ? DAY : HOUR;
  const steps = days ? DAY_STEPS : HOUR_STEPS;
  // Hours land on multiples of the step from Lima midnight (00:00, 06:00, ...).
  // Days start at the first whole day because a step of several days has no natural calendar anchor.
  const firstOf = (step: number) => {
    const grid = (days ? 1 : step) * unit;
    return Math.ceil((start + LIMA_OFFSET) / grid) * grid - LIMA_OFFSET;
  };
  const count = (step: number) => Math.floor((end - firstOf(step)) / (step * unit)) + 1;
  const step = steps.find((one) => count(one) <= max) ?? steps.at(-1) ?? 1;
  const first = firstOf(step);
  const format: Intl.DateTimeFormatOptions = days
    ? { day: "numeric", month: "short" }
    : { hour: "2-digit", minute: "2-digit", hour12: false };

  const label = (t: number) =>
    new Date(t).toLocaleString("en-GB", { timeZone: "America/Lima", ...format });
  // A span shorter than the step holds no whole hour: label where it starts.
  if (count(step) < 1) {
    return [{ t: start, label: label(start) }];
  }
  return Array.from({ length: count(step) }, (_, i) => {
    const t = first + i * step * unit;
    return { t, label: label(t) };
  });
}

export function buildChart(
  series: ChartSeries[],
  width: number,
  height: number,
  maxXTicks = 5,
): Chart {
  const plot = {
    left: MARGIN.left,
    top: MARGIN.top,
    right: width - MARGIN.right,
    bottom: height - MARGIN.bottom,
  };

  const points = series.flatMap((one) => one.points);
  if (points.length === 0) {
    return { width, height, plot, series: [], yTicks: [], xTicks: [] };
  }

  const times = points.map((point) => point.t);
  const startT = Math.min(...times);
  const endT = Math.max(...times);
  const spanMs = endT - startT;
  const axis = priceAxis(
    Math.min(...points.map((point) => point.v)),
    Math.max(...points.map((point) => point.v)),
  );

  const x = (t: number): number =>
    spanMs === 0
      ? (plot.left + plot.right) / 2
      : plot.left + ((t - startT) / spanMs) * (plot.right - plot.left);
  const y = (v: number): number =>
    plot.bottom - ((v - axis.min) / (axis.max - axis.min)) * (plot.bottom - plot.top);

  const drawn: DrawnSeries[] = series
    .filter((one) => one.points.length > 0)
    .map((one) => {
      const dots = one.points.map((point) => ({
        x: round(x(point.t)),
        y: round(y(point.v)),
      }));
      const lastPoint = one.points.at(-1) as ChartPoint;
      return {
        id: one.id,
        label: one.label,
        path: dots.map((dot, i) => `${i === 0 ? "M" : "L"}${dot.x} ${dot.y}`).join(" "),
        dots,
        last: { x: round(x(lastPoint.t)), y: round(y(lastPoint.v)), value: lastPoint.v },
      };
    });

  const decimals = axis.ticks.every((tick) => Math.round(tick * 100) / 100 === tick)
    ? 2
    : 3;
  const ticks =
    spanMs === 0
      ? [
          {
            t: startT,
            label: new Date(startT).toLocaleDateString("en-GB", {
              timeZone: "America/Lima",
              day: "numeric",
              month: "short",
            }),
          },
        ]
      : timeTicks(startT, endT, maxXTicks);

  return {
    width,
    height,
    plot,
    series: drawn,
    yTicks: axis.ticks.map((tick) => ({
      y: round(y(tick)),
      label: tick.toFixed(decimals),
    })),
    xTicks: ticks.map((tick) => {
      const at = round(x(tick.t));
      return {
        x: at,
        label: tick.label,
        anchor:
          at - plot.left < EDGE ? "start" : plot.right - at < EDGE ? "end" : "middle",
      };
    }),
  };
}
