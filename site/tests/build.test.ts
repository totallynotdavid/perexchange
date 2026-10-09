import { type ChildProcess, execFileSync, spawn } from "node:child_process";
import { readdir, rm } from "node:fs/promises";
import { createServer } from "node:net";
import path from "node:path";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { loadLatest } from "../src/lib/load.ts";
import { recordCompleteSnapshot, recordSnapshots } from "./record.ts";
import { scratchDir } from "./scratch.ts";

const SITE = path.resolve(import.meta.dirname, "..");
const SCOPE = " among the houses that answered";

interface Running {
  origin: string;
  dist: string;
  server: ChildProcess;
}

let root: string;
let data: string;
let main: Running;
let complete: Running;

/** The body of a page by the file it would be in a static build, from a running site. */
async function page(file: string, from = main): Promise<string> {
  const response = await fetch(from.origin + "/" + file.replace(/index\.html$/, ""));
  expect(response.status, file).toBe(200);
  return response.text();
}

/** Build from the filesystem root to verify that data paths use the site root. */
function build(dataDir: string, outDir: string): void {
  execFileSync(
    path.join(SITE, "node_modules/.bin/astro"),
    ["build", "--root", SITE, "--outDir", outDir, "--silent"],
    {
      cwd: path.parse(SITE).root,
      env: { ...process.env, PEREXCHANGE_DATA: path.relative(SITE, dataDir) },
      stdio: "pipe",
    },
  );
}

async function freePort(): Promise<number> {
  const probe = createServer();
  await new Promise<void>((resolve) => probe.listen(0, "127.0.0.1", resolve));
  const address = probe.address();
  await new Promise((resolve) => probe.close(resolve));
  return typeof address === "object" && address !== null ? address.port : 0;
}

async function serve(dist: string): Promise<Running> {
  const port = await freePort();
  const server = spawn("node", [path.join(dist, "server/entry.mjs")], {
    env: { ...process.env, HOST: "127.0.0.1", PORT: String(port) },
    stdio: "ignore",
  });
  const origin = `http://127.0.0.1:${port}`;
  for (let attempt = 0; attempt < 100; attempt++) {
    if (server.exitCode !== null) {
      throw new Error("the site server exited");
    }
    if (
      await fetch(origin).then(
        () => true,
        () => false,
      )
    ) {
      return { origin, dist, server };
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("the site server did not start");
}

/** What a reader sees, if every tag were removed and the text left where it was. */
const text = (html: string) =>
  html
    .replace(/<(script|style)[\s\S]*?<\/\1>/g, "")
    .replace(/<[^>]+>/g, "")
    .replace(/\s+/g, " ");

beforeAll(async () => {
  root = await scratchDir("build");
  data = path.join(root, "data");
  recordSnapshots(data);
  build(data, path.join(root, "dist"));
  main = await serve(path.join(root, "dist"));

  const completeData = path.join(root, "complete-data");
  recordCompleteSnapshot(completeData);
  build(completeData, path.join(root, "complete-dist"));
  complete = await serve(path.join(root, "complete-dist"));
}, 240_000);

afterAll(async () => {
  main?.server.kill();
  complete?.server.kill();
  await rm(root, { recursive: true, force: true });
});

describe("the site built from a recorded snapshot", () => {
  it("serves the snapshot as /data/latest.json", async () => {
    const served = JSON.parse(await page("data/latest.json"));

    expect(served).toEqual(await loadLatest(data));
  });

  it("builds the static pages and a server for the rates pages", async () => {
    const files = await readdir(path.join(main.dist, "client"), { recursive: true });

    expect(files).toContain(path.join("docs", "index.html"));
    expect(files).toContain("404.html");
    expect(await page("index.html")).toMatch(/^<!DOCTYPE html>/i);
  });

  it("lists the recorded house with its prices on the rates page", async () => {
    const home = text(await page("index.html"));

    expect(home).toContain("cambiafx");
    expect(home).toContain("3.4360");
    expect(home).toContain("3.4500");
  });

  it("says beside the best prices which source did not answer", async () => {
    const home = text(await page("index.html"));

    expect(home).toContain(
      "1 source did not answer in this snapshot (cambiomundial). " +
        "Their prices are not counted, so a better price may exist.",
    );
  });

  it("claims a best price only among the houses that answered", async () => {
    const claim =
      /(Cheapest place to buy US\$1|Best place to sell US\$1|best current price|Best rate|best to buy|best to sell|lowest current price)(?! among the houses that answered)/;
    const pages = ["index.html", "house/cambiafx/index.html"];

    for (const file of pages) {
      const html = await page(file);

      expect(text(html), file).not.toMatch(claim);
      expect(text(html), file).toContain(SCOPE);
    }
    const home = await page("index.html");
    expect(home).toContain(`the best place to sell${SCOPE}. A converter`);
    expect(text(await page("house/cambiafx/index.html"))).toContain(
      `The lowest current price${SCOPE}`,
    );
  });

  it("claims the cheapest and the best without a qualifier when every source answered", async () => {
    const home = text(await page("index.html", complete));

    expect(home).toContain("Cheapest place to buy US$1 S/");
    expect(home).toContain("Best place to sell US$1 S/");
    expect(home).toContain("Best rate");
    expect(home).not.toMatch(
      /(Cheapest place to buy US\$1|Best place to sell US\$1|best current price|Best rate)( among)/,
    );
    expect(home).not.toContain("did not answer");
  });

  it("has a page and a chart for each recorded house", async () => {
    const html = await page("house/cambiafx/index.html");

    expect(html).toContain('id="chart-24h"');
    expect(html).toContain("<svg");
    expect(text(html)).toContain("2 snapshots in this range");
  });

  it("keeps a space wherever a line break meets a tag", async () => {
    const home = text(await page("index.html"));

    expect(home).toContain("open-source perexchange library");
    expect(home).toMatch(/from perexchange \d/);
    expect(home).toMatch(/\d\. Raw data/);
  });

  it("renders the library docs from the repository's own Markdown", async () => {
    const docs = await page("docs/api/index.html");

    expect(text(docs)).toContain("fetch_rates_report");
    expect(docs).not.toContain("](docs/");
  });

  it("has no inline script, which the content security policy forbids", async () => {
    for (const file of ["index.html", "house/cambiafx/index.html", "docs/index.html"]) {
      const html = await page(file);
      const inline = html.match(
        /<script(?![^>]*\bsrc=)(?![^>]*application\/json)[^>]*>/g,
      );

      expect(inline, file).toBeNull();
    }
  });

  it("answers 404 with the 404 page, also for a house that is not in the snapshot", async () => {
    for (const pathname of ["/nope/", "/house/nope/"]) {
      const response = await fetch(main.origin + pathname);

      expect(response.status, pathname).toBe(404);
      expect(text(await response.text()), pathname).toContain("Page not found");
    }
  });
});
