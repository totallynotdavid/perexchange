import { readFile, rm } from "node:fs/promises";
import { createServer } from "node:http";
import type { AddressInfo } from "node:net";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { loadHistory, loadLatest } from "../src/lib/load.ts";
import { DEAD_AFTER_MINUTES, houseSeries, rank } from "../src/lib/market.ts";
import { recordSnapshots } from "./record.ts";
import { scratchDir } from "./scratch.ts";

let dir: string;

beforeEach(async () => {
  dir = await scratchDir("data");
  recordSnapshots(dir);
});

afterEach(async () => {
  await rm(dir, { recursive: true, force: true });
});

describe("data written by tools/snapshot.py", () => {
  it("loads as the newest fetch, with its failures", async () => {
    const latest = await loadLatest(dir);

    expect(latest.generated_at).toBe("2026-10-08T12:15:00Z");
    expect(latest.rates.map((rate) => rate.id)).toEqual(["cambiafx"]);
    expect(latest.failures).toEqual([
      {
        source: "cambiomundial",
        reason: "blocked",
        message: "403 Forbidden",
      },
    ]);
  });

  it("loads every fetch of the day as history", async () => {
    const { snapshots, skippedLines } = await loadHistory(dir);

    expect(skippedLines).toBe(0);
    expect(snapshots).toHaveLength(2);
    expect(Object.keys(snapshots[0].prices)).toEqual([
      "cambiafx",
      "gordito-digital",
      "chapacambio",
    ]);
  });

  it("records a house gone stale with its age, which the series leaves out", async () => {
    const { snapshots } = await loadHistory(dir);

    expect(snapshots[0].prices.chapacambio.ageMinutes).toBeGreaterThan(
      DEAD_AFTER_MINUTES,
    );
    expect(houseSeries(snapshots, "chapacambio")).toEqual([]);
  });

  it("follows one house across fetches", async () => {
    const { snapshots } = await loadHistory(dir);

    expect(
      houseSeries(snapshots, "cambiafx").map((point) => point.sell),
    ).toEqual([3.458, 3.45]);
  });

  it("ranks the newest fetch", async () => {
    const latest = await loadLatest(dir);

    expect(rank(latest.rates, "buy", latest.generated_at)[0].sell).toBe(3.45);
  });
});

describe("data published at a URL", () => {
  it("loads like the directory it was copied from, reading only the last days", async () => {
    const served = createServer((request, response) => {
      readFile(path.join(dir, request.url ?? ""), "utf8").then(
        (body) => response.end(body),
        () => response.writeHead(404).end(),
      );
    });
    await new Promise<void>((resolve) =>
      served.listen(0, "127.0.0.1", resolve),
    );
    const { port } = served.address() as AddressInfo;
    const url = `http://127.0.0.1:${port}`;

    try {
      const now = new Date("2026-10-09T01:00:00Z");

      expect(await loadLatest(url)).toEqual(await loadLatest(dir));
      expect(await loadHistory(url, now)).toEqual(await loadHistory(dir));
      expect(
        (await loadHistory(url, new Date("2026-12-31T00:00:00Z"))).snapshots,
      ).toEqual([]);
    } finally {
      served.close();
    }
  });
});

describe("reading a longer history from a URL", () => {
  const line = (t: string) => `{"t":"${t}","r":{"a":[3.4,3.45,0]},"f":[]}\n`;
  const files: Record<string, string> = {
    "/history/2026-10-08.jsonl": line("2026-10-08T12:00:00Z"),
    "/history/2026-08-29.jsonl": line("2026-08-29T12:00:00Z"),
    "/history/2026-04-01.jsonl": line("2026-04-01T12:00:00Z"),
  };

  async function withServer<T>(
    use: (url: string, asked: string[]) => Promise<T>,
  ) {
    const asked: string[] = [];
    const served = createServer((request, response) => {
      asked.push(request.url ?? "");
      const body = files[request.url ?? ""];
      if (body === undefined) {
        response.writeHead(404).end();
      } else {
        response.end(body);
      }
    });
    await new Promise<void>((resolve) =>
      served.listen(0, "127.0.0.1", resolve),
    );
    try {
      return await use(
        `http://127.0.0.1:${(served.address() as AddressInfo).port}`,
        asked,
      );
    } finally {
      served.close();
    }
  }

  const now = new Date("2026-10-08T13:00:00Z");

  it("reads past 30 days when asked, and stops at a month with no file", async () => {
    await withServer(async (url, asked) => {
      const { snapshots } = await loadHistory(url, now, 365);

      expect(
        snapshots.map((snapshot) =>
          new Date(snapshot.t).toISOString().slice(0, 10),
        ),
      ).toEqual(["2026-08-29", "2026-10-08"]);
      expect(asked).toHaveLength(90);
    });
  });

  it("reads only the last 30 days by default", async () => {
    await withServer(async (url, asked) => {
      const { snapshots } = await loadHistory(url, now);

      expect(snapshots).toHaveLength(1);
      expect(asked).toHaveLength(30);
    });
  });
});

describe("loading an empty data directory", () => {
  it("names the command that records a snapshot", async () => {
    await expect(loadLatest(path.join(dir, "missing"))).rejects.toThrow(
      /mise run data:site/,
    );
  });

  it("has no history", async () => {
    expect((await loadHistory(path.join(dir, "missing"))).snapshots).toEqual(
      [],
    );
  });
});
