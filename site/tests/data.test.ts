import { describe, expect, it } from "vitest";

import { parseHistory, parseLatest } from "../src/lib/data.ts";

const LATEST = {
  generated_at: "2026-10-08T14:30:00Z",
  library_version: "2.0.0",
  rates: [
    {
      id: "a",
      source: "a",
      name: "a",
      buy: 3.4,
      sell: 3.45,
      timestamp: "2026-10-08T14:30:00Z",
    },
  ],
  failures: [{ source: "b", error_type: "HTTPStatusError", message: "403 Forbidden" }],
};

describe("parseLatest", () => {
  it("reads a snapshot with its rates and failures", () => {
    const latest = parseLatest(JSON.stringify(LATEST));

    expect(latest.rates).toHaveLength(1);
    expect(latest.rates[0].sell).toBe(3.45);
    expect(latest.failures[0].message).toBe("403 Forbidden");
  });

  it("rejects a rate whose price is not a positive number", () => {
    const broken = { ...LATEST, rates: [{ ...LATEST.rates[0], sell: 0 }] };

    expect(() => parseLatest(JSON.stringify(broken))).toThrow(/malformed rate/);
  });

  it("rejects a document that is not a snapshot", () => {
    expect(() => parseLatest("[]")).toThrow(/not a perexchange snapshot/);
    expect(() => parseLatest("{")).toThrow();
  });
});

describe("parseHistory", () => {
  const line = (t: string, prices: Record<string, number[]>) =>
    JSON.stringify({ t, r: prices });

  it("returns snapshots in time order across day files", () => {
    const later = line("2026-10-09T00:10:00Z", { a: [3.4, 3.45, 0] });
    const earlier = [
      line("2026-10-08T23:55:00Z", { a: [3.41, 3.46, 0] }),
      line("2026-10-08T23:40:00Z", { a: [3.42, 3.47, 0] }),
    ].join("\n");

    const { snapshots } = parseHistory([later + "\n", earlier + "\n"]);

    expect(snapshots.map((s) => s.prices.a.sell)).toEqual([3.47, 3.46, 3.45]);
  });

  it("skips and counts a half-written or malformed line without losing the rest", () => {
    const good = line("2026-10-08T00:00:00Z", { a: [3.4, 3.45, 5] });
    const text = [good, '{"t":"2026-10-08T00:15:00Z","r":{"a":[3.4', "null", ""].join(
      "\n",
    );

    const history = parseHistory([text]);

    expect(history.snapshots).toHaveLength(1);
    expect(history.snapshots[0].prices.a.ageMinutes).toBe(5);
    expect(history.skippedLines).toBe(2);
  });

  it("skips a line with a price that is not positive", () => {
    const text = line("2026-10-08T00:00:00Z", { a: [0, 3.45, 0] });

    expect(parseHistory([text]).skippedLines).toBe(1);
  });

  it("treats a missing age as a current quote", () => {
    const text = line("2026-10-08T00:00:00Z", { a: [3.4, 3.45] });

    expect(parseHistory([text]).snapshots[0].prices.a.ageMinutes).toBe(0);
  });
});
