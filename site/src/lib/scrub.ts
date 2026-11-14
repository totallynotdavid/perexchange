import type { Reading } from "./chart-data.ts";
import { formatPrice } from "./format.ts";

interface Scale {
  left: number;
  right: number;
  top: number;
  bottom: number;
  start: number;
  end: number;
  low: number;
  high: number;
}

interface Series {
  id: string;
  points: Reading[];
}

const MINUTE = 60_000;
/** The time label is written inward from the plot's edge when the guide sits this close to it, as a share of the width. */
const EDGE = 0.08;

/** The index of the reading nearest to `minute`. `points` is sorted by time and not empty. */
function nearest(points: Reading[], minute: number): number {
  let low = 0;
  let high = points.length - 1;
  while (low < high) {
    const mid = (low + high) >> 1;
    if ((points[mid] as Reading)[0] < minute) {
      low = mid + 1;
    } else {
      high = mid;
    }
  }
  const before = points[low - 1];
  return before !== undefined &&
    minute - before[0] < (points[low] as Reading)[0] - minute
    ? low - 1
    : low;
}

function across(scale: Scale, minute: number): number {
  const span = scale.end - scale.start;
  const share = span === 0 ? 0.5 : (minute * MINUTE - scale.start) / span;
  return scale.left + share * (scale.right - scale.left);
}

function down(scale: Scale, value: number): number {
  const span = scale.high - scale.low;
  return (
    scale.bottom - ((value - scale.low) / span) * (scale.bottom - scale.top)
  );
}

const percent = (share: number) => `${(share * 100).toFixed(2)}%`;

function limaTime(minute: number): string {
  return new Date(minute * MINUTE).toLocaleString("en-GB", {
    timeZone: "America/Lima",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

/** Shows the readings at `index` of the lead series in one frame, or the latest when `index` is null. */
function show(
  figure: HTMLElement,
  frame: HTMLElement,
  series: Series[],
  index: number | null,
): void {
  const lead = series[0] as Series;
  const scale = JSON.parse(frame.dataset.scale ?? "{}") as Scale;
  const slider = frame.querySelector<HTMLElement>(".scrub");
  const guide = frame.querySelector<HTMLElement>(".guide");
  const when = frame.querySelector<HTMLElement>(".when");
  if (slider === null || guide === null || when === null) {
    return;
  }
  const at = lead.points[index ?? lead.points.length - 1] as Reading;
  const scrubbing = index !== null;
  figure.toggleAttribute("data-scrubbing", scrubbing);
  guide.hidden = !scrubbing;
  when.hidden = !scrubbing;

  const x = across(scale, at[0]);
  guide.style.left = percent(x);
  when.textContent = limaTime(at[0]);
  when.dataset.anchor =
    x - scale.left < EDGE ? "start" : scale.right - x < EDGE ? "end" : "middle";
  when.style.left = percent(x);

  const said: string[] = [];
  for (const one of series) {
    const point = one.points[nearest(one.points, at[0])] as Reading;
    const marker = frame.querySelector<HTMLElement>(
      `.marker[data-series="${one.id}"]`,
    );
    if (marker !== null) {
      marker.hidden = !scrubbing;
      marker.style.left = percent(across(scale, point[0]));
      marker.style.top = percent(down(scale, point[1]));
    }
    const reading = figure.querySelector<HTMLElement>(
      `.reading[data-series="${one.id}"]`,
    );
    const value = reading?.querySelector<HTMLElement>("[data-value]");
    if (value) {
      value.textContent = formatPrice(point[1]);
    }
    const name = reading
      ?.querySelector<HTMLElement>(".name")
      ?.textContent?.trim();
    said.push(`${name ?? one.id} ${formatPrice(point[1])}`);
  }

  const position = index ?? lead.points.length - 1;
  slider.setAttribute("aria-valuenow", String(position));
  slider.setAttribute(
    "aria-valuetext",
    `${scrubbing ? limaTime(at[0]) : "Latest"}: ${said.join(", ")}`,
  );
}

function bindFrame(
  figure: HTMLElement,
  frame: HTMLElement,
  series: Series[],
): void {
  const slider = frame.querySelector<HTMLElement>(".scrub");
  const lead = series[0] as Series;
  if (slider === null) {
    return;
  }
  const scale = JSON.parse(frame.dataset.scale ?? "{}") as Scale;
  const last = lead.points.length - 1;
  let index: number | null = null;
  const set = (next: number | null) => {
    index = next === null ? null : Math.min(last, Math.max(0, next));
    show(figure, frame, series, index);
  };

  const fromPointer = (event: PointerEvent) => {
    const box = slider.getBoundingClientRect();
    const share = (event.clientX - box.left) / box.width;
    const time =
      scale.start +
      ((share - scale.left) / (scale.right - scale.left)) *
        (scale.end - scale.start);
    set(nearest(lead.points, time / MINUTE));
  };
  slider.addEventListener("pointermove", fromPointer);
  slider.addEventListener("pointerdown", fromPointer);
  slider.addEventListener("pointerleave", () => set(null));
  slider.addEventListener("blur", () => set(null));
  slider.addEventListener("keydown", (event) => {
    const from = index ?? last;
    const moves: Record<string, number> = {
      ArrowLeft: from - 1,
      ArrowDown: from - 1,
      ArrowRight: from + 1,
      ArrowUp: from + 1,
      Home: 0,
      End: last,
    };
    const next = moves[event.key];
    if (next === undefined) {
      return;
    }
    event.preventDefault();
    set(index === null && event.key.startsWith("Arrow") ? last : next);
  });
}

/** Lets a pointer or the arrow keys pick a reading on every chart under `root`. */
export function bindCharts(root: ParentNode): void {
  for (const figure of root.querySelectorAll<HTMLElement>(
    "figure[data-readings]",
  )) {
    const series = (
      JSON.parse(figure.dataset.readings ?? "[]") as Series[]
    ).filter((one) => one.points.length > 0);
    if (series.length === 0) {
      continue;
    }
    for (const frame of figure.querySelectorAll<HTMLElement>(
      ".plot-frame[data-scale]",
    )) {
      bindFrame(figure, frame, series);
    }
  }
}
