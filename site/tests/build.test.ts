import { type ChildProcess, execFileSync, spawn } from "node:child_process";
import { readdir, rm } from "node:fs/promises";
import { createServer } from "node:net";
import path from "node:path";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { loadLatest } from "../src/lib/load.ts";
import { recordCompleteSnapshot, recordSnapshots } from "./record.ts";
import { scratchDir } from "./scratch.ts";

const SITE = path.resolve(import.meta.dirname, "..");

interface Running {
  origin: string;
  dist: string;
  server: ChildProcess;
}

let root: string;
let data: string;
let main: Running;
let complete: Running;
let empty: Running;

/** Fetch the URL that corresponds to a static-build file from a running site. */
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

  build(path.join(root, "no-data"), path.join(root, "empty-dist"));
  empty = await serve(path.join(root, "empty-dist"));
}, 360_000);

afterAll(async () => {
  main?.server.kill();
  complete?.server.kill();
  empty?.server.kill();
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

  it("leads with the best rate on each side, the house, and how old the rate is", async () => {
    const home = text(await page("index.html"));

    expect(home).toMatch(
      /Cheapest place to buy dollars S\/ 3\.4500 CambiaFX, \d+ (min|h|d) ago/,
    );
    expect(home).toMatch(
      /Best place to sell dollars S\/ 3\.4360 CambiaFX, \d+ (min|h|d) ago/,
    );
  });

  it("warns that old data is old, naming how old", async () => {
    const html = await page("index.html");
    const notice = html.match(/<p class="notice"[^>]*>/)?.[0] ?? "";

    expect(notice).toContain("data-since");
    expect(notice).not.toContain("hidden");
    expect(text(html)).toMatch(
      /These rates were fetched \d+ (h|d) ago\. The refresh is running late/,
    );
  });

  it("says which house is missing, why, and since when", async () => {
    const home = text(await page("index.html"));

    expect(home).toContain("1 house is not compared");
    expect(home).toContain(
      "Cambio Mundial: Blocks requests from our server since 8 Oct.",
    );
  });

  it("shows no count of failures to a visitor when every source answered", async () => {
    const home = text(await page("index.html", complete));

    expect(home).not.toContain("not compared");
    expect(home).toMatch(/Cheapest place to buy dollars S\/ 3\.4550 Gordito digital/);
    expect(home).toMatch(/Best place to sell dollars S\/ 3\.4410 Western Union/);
  });

  it("lists ten houses and keeps the rest behind a disclosure", async () => {
    const html = await page("index.html", complete);
    const buy = html
      .slice(html.indexOf('class="panel" data-side="buy"'))
      .split("</section>")[0];
    const [shown, rest] = buy.split("<details");

    expect(shown.match(/<tbody>[\s\S]*<\/tbody>/)?.[0].match(/<tr>/g)).toHaveLength(10);
    expect(text(rest)).toContain("Show the other 3 houses");
    expect(rest.match(/<tr>/g)).toHaveLength(3 + 1);
  });

  it("ranks a house's own rate and keeps its special rates on its own page", async () => {
    const home = text(await page("index.html", complete));
    const house = text(await page("house/tkambio/index.html", complete));

    expect(home).not.toContain("5,000");
    expect(house).toContain("Other rates from TKambio");
    expect(house).toContain("from US$5,000");
  });

  it("shows two numbers and the place on a house page", async () => {
    const html = text(await page("house/cambiafx/index.html", complete));

    expect(html).toContain(
      "To buy dollars, you pay S/ 3.4580 No. 2 of 13, S/ 0.0030 behind the best",
    );
    expect(html).toContain("To sell dollars, you get S/ 3.4300");
  });

  it("has a page and a chart for each recorded house", async () => {
    const html = await page("house/cambiafx/index.html");

    expect(html).toContain('id="chart-24h"');
    expect(html).toContain("<svg");
    expect(text(html)).toContain("2 readings in this range");
  });

  it("keeps a space wherever a line break meets a tag", async () => {
    const home = text(await page("index.html"));

    expect(home).toMatch(/fetched \d+ \w+ ago\. The refresh/);
    expect(home).toContain("not offers. Open data");
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

  it("says the rates are not available, with a 503, when there is no snapshot", async () => {
    for (const pathname of ["/", "/house/cambiafx/"]) {
      const response = await fetch(empty.origin + pathname);
      const html = await response.text();

      expect(response.status, pathname).toBe(503);
      expect(text(html), pathname).toContain("Rates are not available right now");
      expect(html, pathname).toContain('role="alert"');
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
