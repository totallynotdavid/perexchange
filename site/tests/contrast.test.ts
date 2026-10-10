import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

type Rgb = [number, number, number];
type Scheme = "light" | "dark";

const tokensCss = readFileSync(
  path.resolve(import.meta.dirname, "../src/styles/tokens.css"),
  "utf8",
);

/** Read both colors from a light-dark token, or use one color for both schemes. */
function token(name: string): Record<Scheme, string> {
  const match = tokensCss.match(new RegExp(`--${name}:\\s*([^;]+);`));
  if (match === null) {
    throw new Error(`no token named --${name}`);
  }
  const pair = match[1].match(/^light-dark\((.+)\)$/);
  if (pair === null) {
    return { light: match[1], dark: match[1] };
  }
  const [light, dark] = pair[1].split(/,\s*(?=#|oklch)/);
  return { light, dark };
}

const linear = (v: number) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);

/** Convert a hex or OKLCH token to linear-light sRGB. */
function parse(color: string): Rgb {
  const hex = color.match(/^#([0-9a-f]{6})$/i);
  if (hex) {
    return [0, 2, 4].map((i) =>
      linear(parseInt(hex[1].slice(i, i + 2), 16) / 255),
    ) as Rgb;
  }
  const lch = color.match(/^oklch\(([\d.]+) ([\d.]+) ([\d.]+)\)$/);
  if (lch === null) {
    throw new Error(`cannot read the color ${color}`);
  }
  const [l, c, h] = lch.slice(1).map(Number);
  const a = c * Math.cos((h * Math.PI) / 180);
  const b = c * Math.sin((h * Math.PI) / 180);
  const l3 = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m3 = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s3 = (l - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const rgb: Rgb = [
    4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3,
    -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3,
    -0.0041960863 * l3 - 0.7034186147 * m3 + 1.707614701 * s3,
  ];
  return rgb.map((v) => Math.min(1, Math.max(0, v))) as Rgb;
}

const luminance = ([r, g, b]: Rgb) => 0.2126 * r + 0.7152 * g + 0.0722 * b;

function ratio(foreground: string, background: string, scheme: Scheme): number {
  const [high, low] = [
    luminance(parse(token(foreground)[scheme])),
    luminance(parse(token(background)[scheme])),
  ].sort((a, b) => b - a);
  return (high + 0.05) / (low + 0.05);
}

// WCAG 2.2 requires 4.5:1 for text and 3:1 for meaningful edges and lines.
const TEXT: [string, string][] = [
  ["fg", "bg"],
  ["fg", "bg-subtle"],
  ["fg", "bg-muted"],
  ["fg-secondary", "bg"],
  ["fg-secondary", "bg-subtle"],
  ["fg-muted", "bg"],
  ["fg-muted", "bg-subtle"],
  ["fg-muted", "bg-muted"],
  ["accent", "bg"],
  ["accent", "bg-subtle"],
  ["warn", "bg"],
  ["warn", "bg-muted"],
  ["warn", "warn-bg"],
  ["danger", "danger-bg"],
  ["positive", "positive-bg"],
  ["positive", "bg"],
];

const GRAPHICS: [string, string][] = [
  ["border-control", "bg"],
  ["border-control", "bg-subtle"],
  ["accent", "bg"],
  ["accent", "bg-subtle"],
  // The chart sits on the page background.
  ["chart-buy", "bg"],
];

describe.each<Scheme>(["light", "dark"])("the %s palette", (scheme) => {
  it.each(TEXT)("reads %s on %s at 4.5:1 or more", (foreground, background) => {
    expect(ratio(foreground, background, scheme)).toBeGreaterThanOrEqual(4.5);
  });

  it.each(GRAPHICS)("shows %s against %s at 3:1 or more", (foreground, background) => {
    expect(ratio(foreground, background, scheme)).toBeGreaterThanOrEqual(3);
  });
});
