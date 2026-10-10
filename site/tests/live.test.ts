import { describe, expect, it } from "vitest";

import { refreshAges } from "../src/lib/live.ts";

const NOW = Date.parse("2026-10-08T15:00:00Z");

function age(isoTime: string) {
  const classes = new Set<string>();
  return {
    dateTime: isoTime,
    textContent: "",
    classList: {
      toggle: (name: string, on: boolean) =>
        on ? classes.add(name) : classes.delete(name),
    },
    classes,
  };
}

function notice(since: string) {
  return { dataset: { since }, hidden: true };
}

function page(ages: ReturnType<typeof age>[], notices: ReturnType<typeof notice>[]) {
  return {
    querySelectorAll: (selector: string) =>
      selector.startsWith("time") ? ages : notices,
  } as unknown as ParentNode;
}

describe("refreshAges", () => {
  it("rewrites each age from the time it counts from", () => {
    const ages = [
      age("2026-10-08T14:48:00Z"),
      age("2026-10-08T09:00:00Z"),
      age("2026-10-08T14:59:40Z"),
    ];

    refreshAges(page(ages, []), NOW);

    expect(ages.map((one) => one.textContent)).toEqual([
      "12 min ago",
      "6 h ago",
      "just now",
    ]);
  });

  it("marks an age as old once it reaches the limit, and unmarks it when it is not", () => {
    const fresh = age("2026-10-08T14:00:00Z");
    const old = age("2026-10-08T12:00:00Z");
    old.classes.add("stale-before");

    refreshAges(page([fresh, old], []), NOW);

    expect([fresh.classes.has("old"), old.classes.has("old")]).toEqual([false, true]);
  });

  it("shows a notice only once the data it watches is old enough", () => {
    const fresh = notice("2026-10-08T14:30:00Z");
    const old = notice("2026-10-08T11:00:00Z");

    refreshAges(page([], [fresh, old]), NOW);

    expect([fresh.hidden, old.hidden]).toEqual([true, false]);
  });
});
