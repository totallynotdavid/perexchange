import { type ChildProcess, execFileSync, spawn } from "node:child_process";
import { readdir, rm } from "node:fs/promises";
import { createServer } from "node:net";
import path from "node:path";

import { Window } from "happy-dom";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { bindBoard } from "../src/lib/calculator.ts";
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

    expect(shown.match(/<tbody>[\s\S]*<\/tbody>/)?.[0].match(/<tr[ >]/g)).toHaveLength(
      10,
    );
    expect(text(rest)).toContain("Show the other 3 houses");
    expect(rest.match(/<tr[ >]/g)).toHaveLength(3 + 1);
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

    expect(html).toContain('id="chart-house-24h"');
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

type Storage = "open" | "blocked" | "full";

async function openHome(stored: Record<string, string> = {}, storage: Storage = "open") {
  const win = new Window({ url: `${complete.origin}/` });
  for (const [key, value] of Object.entries(stored)) {
    win.localStorage.setItem(key, value);
  }
  if (storage === "blocked") {
    Object.defineProperty(win, "localStorage", {
      get() {
        throw new Error("blocked");
      },
    });
  }
  if (storage === "full") {
    // A browser in private mode or with a full quota reads but refuses to write.
    Object.defineProperty(win, "localStorage", {
      value: {
        getItem: (key: string) => stored[key] ?? null,
        setItem() {
          throw new Error("QuotaExceededError");
        },
      },
    });
  }
  win.document.write(await page("index.html", complete));
  bindBoard(win.document as unknown as Document);

  const panel = (side: string) =>
    win.document.querySelector(`.panel[data-side="${side}"]`)!;
  const field = (side: string) => panel(side).querySelector("input[type='text']")!;
  const type = (side: string, value: string) => {
    const input = field(side);
    input.value = value;
    input.dispatchEvent(new win.Event("input", { bubbles: true }));
  };
  return {
    win,
    field,
    type,
    summary: (side = "buy") => panel(side).querySelector("output")!.value,
    rows: () =>
      [...panel("buy").querySelectorAll("tr[data-rate]")].map((row) => ({
        house: row.getAttribute("data-house"),
        rate: row.querySelector(".price")!.textContent,
        total: row.querySelector("[data-total]")!.textContent,
        edge: row.querySelector("[data-edge]")!.textContent,
      })),
    heads: () =>
      [...panel("buy").querySelectorAll("thead")].map((head) =>
        text(head.innerHTML).trim(),
      ),
    chooseMode: (mode: "usd" | "pen") =>
      (
        win.document.getElementById(`mode-${mode}`) as unknown as HTMLInputElement
      ).click(),
  };
}

describe("the buy calculator on the served home page", () => {
  it("prices US$200 at every house before anyone types, cheapest first", async () => {
    const home = await openHome();
    const rows = home.rows();

    expect(rows).toHaveLength(13);
    expect(rows[0]).toEqual({
      house: "Gordito digital",
      rate: "3.4550",
      total: "691.00",
      edge: "5.00",
    });
    expect(rows[12]).toMatchObject({
      house: "Western Union",
      rate: "3.4800",
      total: "696.00",
      edge: "–",
    });
    expect((home.field("buy") as unknown as HTMLInputElement).value).toBe("200");
    expect(home.summary()).toBe(
      "US$200.00 costs S/ 691.00 at Gordito digital. That is S/ 5.00 less than at Western Union, the dearest.",
    );
  });

  it("shows the default amounts in the page itself, for a browser without scripts", async () => {
    const html = text(await page("index.html", complete));

    expect(html).toContain("You pay S/ for US$200.00");
    expect(html).toContain("US$200.00 costs S/ 691.00 at Gordito digital");
  });

  it("says which side of the spread each rate is", async () => {
    const home = await openHome();

    expect(home.heads().join(" ")).toContain("Sell rate you pay per US$1");
    expect(text(await page("index.html", complete))).toContain(
      "Buy rate you get per US$1",
    );
  });

  it("follows the amount typed, with grouping and cents", async () => {
    const home = await openHome();
    home.type("buy", "1,250.50");
    const rows = home.rows();

    expect(rows[0]?.total).toBe("4,320.48");
    expect(rows[12]?.total).toBe("4,351.74");
    expect(rows[0]?.edge).toBe("31.26");
    expect(home.summary()).toContain("US$1,250.50 costs S/ 4,320.48");
  });

  it("updates the houses behind the disclosure as well", async () => {
    const home = await openHome();
    home.type("buy", "10");

    expect(home.rows().every((row) => row.total !== "–")).toBe(true);
    expect(home.rows()[11]?.total).toBe("34.78");
  });

  it.each([
    ["200.005", "US$200.01 costs S/ 691.03"],
    ["200.004", "US$200.00 costs S/ 691.00"],
    [".5", "US$0.50 costs S/ 1.73"],
    ["5.", "US$5.00 costs S/ 17.28"],
    ["0.01", "US$0.01 costs S/ 0.03"],
    ["1,000,000,000", "US$1,000,000,000.00 costs S/ 3,455,000,000.00"],
  ])("rounds %s to the cent and prices it", async (typed, expected) => {
    const home = await openHome();
    home.type("buy", typed);

    expect(home.summary()).toContain(expected);
  });

  it("gives every house the same figure when the amount is too small to tell them apart", async () => {
    const home = await openHome();
    home.type("buy", "0.01");

    expect(home.rows().map((row) => row.total)).toEqual(Array(13).fill("0.03"));
    expect(home.summary()).toContain("Every house gives the same at this amount.");
  });

  it.each([
    ["", "Type an amount to see what each house charges."],
    ["   ", "Type an amount to see what each house charges."],
    ["0", "Type an amount above zero."],
    ["0.00", "Type an amount above zero."],
    ["0.004", "Type an amount above zero."],
    ["1,000,000,000.01", "Type 1,000,000,000 or less."],
    ["99999999999999999999999", "Type 1,000,000,000 or less."],
    ["1e9", "Use digits only, for example 200 or 1,250.50."],
    ["-5", "Use digits only, for example 200 or 1,250.50."],
    ["abc", "Use digits only, for example 200 or 1,250.50."],
    ["1.2.3", "Use digits only, for example 200 or 1,250.50."],
  ])("shows no figure for %j and says why", async (typed, hint) => {
    const home = await openHome();
    home.type("buy", typed);

    expect(home.summary()).toBe(hint);
    expect(home.rows().every((row) => row.total === "–" && row.edge === "–")).toBe(true);
  });

  it("marks the field invalid for a mistake and not for an empty field", async () => {
    const home = await openHome();
    const invalid = () => home.field("buy").getAttribute("aria-invalid");

    home.type("buy", "abc");
    expect(invalid()).toBe("true");
    home.type("buy", "");
    expect(invalid()).toBe("false");
  });

  it("turns the field into soles to spend, priced in dollars rounded down", async () => {
    const home = await openHome();
    home.chooseMode("pen");
    const rows = home.rows();

    expect((home.field("buy") as unknown as HTMLInputElement).value).toBe("1000");
    expect(rows[0]).toMatchObject({
      house: "Gordito digital",
      total: "289.43",
      edge: "2.08",
    });
    expect(rows[12]).toMatchObject({ total: "287.35", edge: "–" });
    expect(home.summary()).toBe(
      "S/ 1,000.00 buys US$289.43 at Gordito digital. That is US$2.08 more than at Western Union, the dearest.",
    );
    expect(home.heads().join(" ")).toContain("You get US$ for S/ 1,000.00 Extra");
  });

  it("gives exactly 200.00 dollars for the soles that 200 dollars cost", async () => {
    const home = await openHome();
    home.chooseMode("pen");
    home.type("buy", "691");

    expect(home.rows()[0]?.total).toBe("200.00");
  });

  it("keeps a separate amount for each mode and remembers both", async () => {
    const home = await openHome();
    home.type("buy", "350");
    home.chooseMode("pen");
    home.type("buy", "5,000");
    home.chooseMode("usd");

    expect((home.field("buy") as unknown as HTMLInputElement).value).toBe("350");
    expect(home.win.localStorage.getItem("perexchange:amount:pen")).toBe("5,000");
    expect(home.win.localStorage.getItem("perexchange:mode")).toBe("usd");
  });

  it("opens in the mode and with the amount the visitor left", async () => {
    const home = await openHome({
      "perexchange:mode": "pen",
      "perexchange:amount:pen": "2500",
    });

    expect(home.summary()).toContain("S/ 2,500.00 buys US$723.58 at Gordito digital");
  });

  it("falls back to the default when the saved amount is empty", async () => {
    const home = await openHome({ "perexchange:amount:usd": "" });

    expect((home.field("buy") as unknown as HTMLInputElement).value).toBe("200");
  });

  it("still works when the browser refuses storage", async () => {
    const home = await openHome({}, "blocked");
    home.type("buy", "300");

    expect(home.summary()).toContain("US$300.00 costs S/ 1,036.50");
    home.chooseMode("pen");
    expect(home.summary()).toContain("S/ 1,000.00 buys");
  });

  it("still calculates when the browser reads storage but refuses to write", async () => {
    const home = await openHome({}, "full");
    home.type("buy", "300");

    expect(home.summary()).toContain("US$300.00 costs S/ 1,036.50");
    home.chooseMode("pen");
    expect(home.summary()).toContain("S/ 1,000.00 buys");
    home.chooseMode("usd");
    expect((home.field("buy") as unknown as HTMLInputElement).value).toBe("300");
    home.type("sell", "1,000");
    expect(home.summary("sell")).toBe("You get S/ 3,441.00");
  });

  it("still sells dollars at the best buy rate", async () => {
    const home = await openHome();
    home.type("sell", "1,000");

    expect(home.summary("sell")).toBe("You get S/ 3,441.00");
  });

  it("tells the seller what is wrong with an amount, as the buyer is told", async () => {
    const home = await openHome();
    const flagged = () => home.field("sell").getAttribute("aria-invalid");
    const cases: [string, string, string][] = [
      ["", "", "false"],
      ["0", "Type an amount above zero.", "true"],
      ["12a", "Use digits only, for example 200 or 1,250.50.", "true"],
      ["2000000000", "Type 1,000,000,000 or less.", "true"],
      ["12.5", "You get S/ 43.01", "false"],
    ];

    for (const [typed, said, invalid] of cases) {
      home.type("sell", typed);
      expect(home.summary("sell"), typed).toBe(said);
      expect(flagged(), typed).toBe(invalid);
    }
  });
});

describe("the best-rate chart on the served home page", () => {
  it("draws one line per side, ranged 7 days, 30 days and all, from the recorded runs", async () => {
    const html = await page("index.html", complete);
    const buy = html
      .slice(html.indexOf('class="panel" data-side="buy"'))
      .split("</section>")[0];
    const figure = (range: string) =>
      text(
        buy.match(
          new RegExp(`<figure id="chart-buy-${range}"[\\s\\S]*?</figure>`),
        )?.[0] ?? "",
      );

    expect(text(buy)).toContain("7 days 30 days All");
    expect(figure("7d")).toContain("3 readings in this range");
    expect(figure("30d")).toContain("4 readings in this range");
    expect(figure("all")).toContain("5 readings in this range");
  });

  it("charts the cheapest base rate and never a special rate", async () => {
    const html = await page("index.html", complete);
    const buy = html
      .slice(html.indexOf('class="panel" data-side="buy"'))
      .split("</section>")[0];
    const seven = text(
      buy.match(/<figure id="chart-buy-7d"[\s\S]*?<\/figure>/)?.[0] ?? "",
    );

    expect(seven).toContain("now 3.4550, range 3.4500 to 3.4550");
    expect(text(html)).toContain("now 3.4550, range 3.4500 to 3.4750");
    expect(html).not.toContain("3.4000");
  });

  it("draws a line for the dearest side too", async () => {
    const html = await page("index.html", complete);

    expect(text(html)).toContain("Best price for US$1: now 3.4410");
  });

  it("has a wide and a narrow drawing of each range", async () => {
    const html = await page("index.html", complete);

    expect(html.match(/<svg class="plot wide"/g)).toHaveLength(6);
    expect(html.match(/<svg class="plot narrow"/g)).toHaveLength(6);
  });

  it("shows an empty state, not a line, until two days are recorded", async () => {
    const html = await page("index.html");

    expect(text(html)).toContain(
      "The chart appears once two days of readings are recorded. The first is from 8 Oct.",
    );
    expect(html).not.toContain('<svg class="plot');
    expect(html).not.toContain("chart-block");
  });
});
