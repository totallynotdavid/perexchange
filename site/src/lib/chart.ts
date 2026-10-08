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
  xTicks: { x: number; label: string }[];
}

const MARGIN = { left: 54, top: 10, right: 14, bottom: 26 };
const PRICE_STEPS = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1];
const MAX_Y_TICKS = 6;
const DAY = 86_400_000;

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

function niceStep(span: number): number {
  return PRICE_STEPS.find((step) => span / step <= MAX_Y_TICKS) ?? 1;
}

/** The price axis: a padded range and tick values that land on round numbers. */
export function priceAxis(
  low: number,
  high: number,
): { min: number; max: number; ticks: number[] } {
  const flat = high - low < 0.005;
  const padding = flat ? 0.01 : (high - low) * 0.12;
  const min = low - padding;
  const max = high + padding;
  const step = niceStep(max - min);

  const ticks: number[] = [];
  for (let tick = Math.ceil(min / step) * step; tick <= max + 1e-9; tick += step) {
    ticks.push(Number(tick.toFixed(4)));
  }
  return { min, max, ticks };
}

function timeLabel(t: number, spanMs: number): string {
  const options: Intl.DateTimeFormatOptions =
    spanMs <= 1.5 * DAY
      ? { hour: "2-digit", minute: "2-digit", hour12: false }
      : { day: "numeric", month: "short" };
  return new Date(t).toLocaleString("en-GB", { timeZone: "America/Lima", ...options });
}

export function buildChart(
  series: ChartSeries[],
  width: number,
  height: number,
  xTickCount = 5,
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
  const xTicks =
    spanMs === 0
      ? [{ x: round(x(startT)), label: timeLabel(startT, 0) }]
      : Array.from({ length: xTickCount }, (_, i) => {
          const t = startT + (spanMs * i) / (xTickCount - 1);
          return { x: round(x(t)), label: timeLabel(t, spanMs) };
        });

  return {
    width,
    height,
    plot,
    series: drawn,
    yTicks: axis.ticks.map((tick) => ({
      y: round(y(tick)),
      label: tick.toFixed(decimals),
    })),
    xTicks,
  };
}
