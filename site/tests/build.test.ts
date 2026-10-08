import { execFileSync } from "node:child_process";
import { readFile, readdir, rm } from "node:fs/promises";
import path from "node:path";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { loadLatest } from "../src/lib/load.ts";
import { recordCompleteSnapshot, recordSnapshots } from "./record.ts";
import { scratchDir } from "./scratch.ts";

const SITE = path.resolve(import.meta.dirname, "..");
const SCOPE = " among the houses that answered";

let root: string;
let data: string;
let dist: string;
let completeDist: string;

const page = (file: string, from = dist) => readFile(path.join(from, file), "utf8");

function build(dataDir: string, outDir: string): void {
  execFileSync(
    path.join(SITE, "node_modules/.bin/astro"),
    ["build", "--outDir", outDir, "--silent"],
    { cwd: SITE, env: { ...process.env, PEREXCHANGE_DATA: dataDir }, stdio: "pipe" },
  );
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
  dist = path.join(root, "dist");
  recordSnapshots(data);
  build(data, dist);

  const completeData = path.join(root, "complete-data");
  completeDist = path.join(root, "complete-dist");
  recordCompleteSnapshot(completeData);
  build(completeData, completeDist);
}, 240_000);

afterAll(async () => {
  await rm(root, { recursive: true, force: true });
});

describe("the site built from a recorded snapshot", () => {
  it("serves the snapshot as /data/latest.json", async () => {
    const served = JSON.parse(await page("data/latest.json"));

    expect(served).toEqual(await loadLatest(data));
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
    const home = text(await page("index.html", completeDist));

    expect(home).toContain("Cheapest place to buy US$1 S/");
    expect(home).toContain("Best place to sell US$1 S/");
    expect(home).toContain("Best rate");
    expect(home).not.toMatch(
      /(Cheapest place to buy US\$1|Best place to sell US\$1|best current price|Best rate)( among)/,
    );
    expect(home).not.toContain("did not answer");
  });

  it("has a page and a chart for each recorded house", async () => {
    const houses = await readdir(path.join(dist, "house"));
    const html = await page("house/cambiafx/index.html");

    expect(houses).toContain("cambiafx");
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

  it("has a 404 page", async () => {
    expect(text(await page("404.html"))).toContain("Page not found");
  });
});
