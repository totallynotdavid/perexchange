import { type ChildProcess, execFileSync, spawn } from "node:child_process";
import { readdir, rm } from "node:fs/promises";
import { createServer } from "node:net";
import path from "node:path";

import { Window } from "happy-dom";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { bindBoard } from "../src/lib/calculator.ts";
import { bindSide, storageOf } from "../src/lib/choices.ts";
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

  it("shows the best rate, its house and its age before anyone types", async () => {
    const home = text(await page("index.html"));

    expect(home).toContain("Best rate per US$1 S/ 3.4500 at CambiaFX");
    expect(home).toContain("Best rate per US$1 S/ 3.4360 at CambiaFX");
    expect(home).toMatch(
      /Go to CambiaFX\s*, opens its website Rate from \d+ (min|h|d) ago/,
    );
  });

  it("opens with the page's name and no repeated heading, count or eyebrow", async () => {
    const home = text(await page("index.html"));

    expect(home).toContain("Dollar rates in Peru");
    expect(home).not.toContain("Live market board");
    expect(home).not.toContain("compared, updated");
    expect(home).not.toContain("Coverage");
    expect(home).not.toContain("Open data");
  });

  it("hides the amount field from a browser without scripts, which has the rate to read", async () => {
    const html = await page("index.html", complete);

    expect(html).toMatch(/<div class="amount" hidden/);
    expect(text(html)).toContain("Best rate per US$1 S/ 3.4550 at Gordito digital");
    expect(text(html)).toContain("Best rate per US$1 S/ 3.4410 at Western Union");
  });

  it("tells the reader to check an old rate, in the line that gives its age", async () => {
    const html = await page("index.html");
    const advice = html.match(/<p class="rate-advice"[^>]*>/)?.[0] ?? "";

    expect(advice).toContain("data-since");
    expect(advice).not.toContain("hidden");
    expect(text(html)).toMatch(
      /Rate from \d+ (h|d) ago Check it with the house before you go\./,
    );
  });

  it("says which house is missing and why", async () => {
    const home = text(await page("index.html"));

    expect(home).toContain("1 house is not compared");
    expect(home).toContain("Cambio Mundial: Blocks requests from our server.");
  });

  it("shows no count of failures to a visitor when every source answered", async () => {
    const home = text(await page("index.html", complete));

    expect(home).not.toContain("not compared");
  });

  it("lists five houses and keeps the rest behind a disclosure", async () => {
    const html = await page("index.html", complete);
    const buy = html
      .slice(html.indexOf('class="results" data-side="buy"'))
      .split("</section>")[0];
    const [shown, rest] = buy.split("<details");

    expect(shown.match(/<tbody>[\s\S]*<\/tbody>/)?.[0].match(/<tr[ >]/g)).toHaveLength(5);
    expect(text(rest)).toContain("Show the other 8 houses");
    expect(rest.match(/<tr[ >]/g)).toHaveLength(8 + 1);
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
    expect(text(html)).toMatch(
      /(Up|Down) S\/ 0\.\d{4} \(.*\) in 24 hours, from S\/ 3\.\d{4} to S\/ 3\.\d{4}\./,
    );
  });

  it("leads from a house page to the house's own site", async () => {
    const html = await page("house/cambiafx/index.html");
    const link = html.match(
      /<a class="cta" href="([^"]+)" target="_blank"[^>]*>\s*Go to CambiaFX/,
    );

    expect(link?.[1]).toBe("https://cambiafx.pe/");
  });

  it("puts the age of the rate before the button on a house page", async () => {
    const house = text(await page("house/cambiafx/index.html"));

    expect(house).toMatch(/CambiaFX Rate from \d+ \w+ ago Go to CambiaFX/);
    expect(house).not.toContain("All houses");
  });

  it("renders the library docs from the repository's own Markdown", async () => {
    const docs = await page("docs/api/index.html");

    expect(text(docs)).toContain("fetch_rates_report");
    expect(docs).not.toContain("](docs/");
  });

  it("has no inline script, which the content security policy forbids", async () => {
    for (const file of [
      "index.html",
      "history/index.html",
      "house/cambiafx/index.html",
      "docs/index.html",
    ]) {
      const html = await page(file);
      const inline = html.match(
        /<script(?![^>]*\bsrc=)(?![^>]*application\/json)[^>]*>/g,
      );

      expect(inline, file).toBeNull();
    }
  });

  it("says the rates are not available, with a 503, when there is no snapshot", async () => {
    for (const pathname of ["/", "/history/", "/house/cambiafx/"]) {
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

async function openHome(
  stored: Record<string, string> = {},
  storage: Storage = "open",
  width = 1280,
) {
  const win = new Window({ url: `${complete.origin}/`, width, height: 800 });
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

  const doc = win.document;
  const input = doc.getElementById("amount") as unknown as HTMLInputElement;
  const hero = (side: string) => doc.querySelector(`.hero[data-side="${side}"]`)!;
  const part = (side: string, name: string) =>
    hero(side).querySelector(`[data-part="${name}"]`)!.textContent!;
  const results = (side: string) => doc.querySelector(`.results[data-side="${side}"]`)!;
  return {
    win,
    input,
    hero,
    results,
    type: (value: string) => {
      input.value = value;
      input.dispatchEvent(new win.Event("input", { bubbles: true }));
    },
    chooseSide: (side: "buy" | "sell") =>
      (doc.getElementById(`side-${side}`) as unknown as HTMLInputElement).click(),
    flip: () =>
      (doc.querySelector("[data-unit]") as unknown as HTMLButtonElement).click(),
    unit: () => doc.querySelector("[data-unit-text]")!.textContent,
    fieldLabel: () => doc.querySelector("[data-label]")!.textContent,
    reading: () => doc.querySelector<HTMLElement>(".board")!.dataset.reading,
    /** What the hero says, as a reader gets it. */
    summary: (side = "buy") =>
      hero(side).querySelector("output")!.textContent!.replace(/\s+/g, " ").trim(),
    figure: (side = "buy") => part(side, "figure"),
    note: (side = "buy") => part(side, "note"),
    cta: (side = "buy") => hero(side).querySelector<HTMLAnchorElement>("a.cta")!,
    rows: (side = "buy") =>
      [...results(side).querySelectorAll("tr[data-rate]")].map((row) => ({
        house: row.getAttribute("data-house"),
        rate: row.querySelector(".price")!.textContent,
        total: row.querySelector("[data-total]")!.textContent,
        link: row.querySelector<HTMLAnchorElement>("th a")!,
        late:
          row.querySelector(".late")?.textContent?.replace(/\s+/g, " ").trim() ?? null,
      })),
    head: (side = "buy") =>
      text(results(side).querySelector("thead .total-col")!.innerHTML).trim(),
  };
}

describe("the amount field and the answer on the served home page", () => {
  it("starts with an empty field in focus and the best rate, not an invented amount", async () => {
    const home = await openHome();

    expect(home.input.value).toBe("");
    expect(home.win.document.activeElement).toBe(home.input);
    expect(home.reading()).toBe("empty");
    expect(home.summary()).toBe("Best rate per US$1 S/ 3.4550 at Gordito digital");
    expect(home.rows().map((row) => row.total)).toEqual(Array(13).fill(""));
  });

  it("answers an amount with the sum at the best house and the gap to the dearest", async () => {
    const home = await openHome();
    home.type("200");

    expect(home.reading()).toBe("ok");
    expect(home.summary()).toBe(
      "You pay S/ 691.00 at Gordito digital S/ 5.00 less than at Western Union, which charges the most.",
    );
    expect(home.head()).toBe("You pay for US$200.00");
  });

  it("lists every house cheapest first with its rate and total", async () => {
    const home = await openHome();
    home.type("200");
    const rows = home.rows();

    expect(rows).toHaveLength(13);
    expect(rows[0]).toMatchObject({
      house: "Gordito digital",
      rate: "3.4550",
      total: "691.00",
    });
    expect(rows[12]).toMatchObject({
      house: "Western Union",
      rate: "3.4800",
      total: "696.00",
    });
  });

  it("follows the amount typed, with grouping and cents, in the header too", async () => {
    const home = await openHome();
    home.type("1,250.50");
    const rows = home.rows();

    expect(rows[0]?.total).toBe("4,320.48");
    expect(rows[12]?.total).toBe("4,351.74");
    expect(home.note()).toBe(
      "S/ 31.26 less than at Western Union, which charges the most.",
    );
    expect(home.head()).toBe("You pay for US$1,250.50");
  });

  it("prices the houses behind the disclosure as well", async () => {
    const home = await openHome();
    home.type("10");

    expect(home.rows().every((row) => row.total !== "")).toBe(true);
    expect(home.rows()[11]?.total).toBe("34.78");
  });

  it.each([
    ["200.005", "691.03"],
    ["200.004", "691.00"],
    [".5", "1.73"],
    ["5.", "17.28"],
    ["0.01", "0.03"],
    ["1,000,000,000", "3,455,000,000.00"],
  ])("rounds %s to the cent and prices it", async (typed, expected) => {
    const home = await openHome();
    home.type(typed);

    expect(home.figure()).toBe(expected);
  });

  it("gives every house the same figure when the amount is too small to tell them apart", async () => {
    const home = await openHome();
    home.type("0.01");

    expect(home.rows().map((row) => row.total)).toEqual(Array(13).fill("0.03"));
    expect(home.note()).toBe("Every house gives the same at this amount.");
  });

  it.each([
    ["", ""],
    ["   ", ""],
    ["0", "Type an amount above zero."],
    ["0.00", "Type an amount above zero."],
    ["0.004", "Type an amount above zero."],
    ["1,000,000,000.01", "Type 1,000,000,000 or less."],
    ["99999999999999999999999", "Type 1,000,000,000 or less."],
    ["1e9", "Use digits only, for example 200 or 1,250.50."],
    ["-5", "Use digits only, for example 200 or 1,250.50."],
    ["abc", "Use digits only, for example 200 or 1,250.50."],
    ["1.2.3", "Use digits only, for example 200 or 1,250.50."],
  ])("shows no total for %j and says why", async (typed, hint) => {
    const home = await openHome();
    home.type(typed);

    expect(home.note()).toBe(hint);
    expect(home.summary()).toContain("Best rate per US$1 S/ 3.4550 at Gordito digital");
    expect(home.rows().every((row) => row.total === "")).toBe(true);
  });

  it("marks the field invalid for a mistake and not for an empty field", async () => {
    const home = await openHome();

    home.type("abc");
    expect(home.input.getAttribute("aria-invalid")).toBe("true");
    home.type("");
    expect(home.input.getAttribute("aria-invalid")).toBe("false");
  });

  it("names the field for what the person wants to do", async () => {
    const home = await openHome();

    expect(home.fieldLabel()).toBe("Amount to buy");
    home.chooseSide("sell");
    expect(home.fieldLabel()).toBe("Amount to sell");
  });
});

describe("the unit button on the served home page", () => {
  it("turns the amount into soles at the best rate and prices the soles in dollars", async () => {
    const home = await openHome();
    home.type("200");
    home.flip();

    expect(home.unit()).toBe("S/");
    expect(home.input.value).toBe("691.00");
    expect(home.summary()).toContain("You get US$ 200.00 at Gordito digital");
    expect(home.head()).toBe("You get for S/ 691.00");
    expect(home.rows()[12]?.total).toBe("198.56");
  });

  it("returns the same amount when flipped back", async () => {
    const home = await openHome();
    home.type("200");
    home.flip();
    home.flip();

    expect(home.unit()).toBe("US$");
    expect(home.input.value).toBe("200.00");
  });

  it("leaves an empty or invalid field as it is", async () => {
    const home = await openHome();
    home.flip();
    expect(home.input.value).toBe("");

    home.type("abc");
    home.flip();
    expect(home.input.value).toBe("abc");
    expect(home.input.getAttribute("aria-invalid")).toBe("true");
  });

  it("rounds the dollars received down, so the figure is never more than the soles buy", async () => {
    const home = await openHome({
      "perexchange:unit": "pen",
      "perexchange:amount": "2500",
    });

    expect(home.summary()).toContain("You get US$ 723.58 at Gordito digital");
  });

  it("gives exactly 200.00 dollars for the soles that 200 dollars cost", async () => {
    const home = await openHome({ "perexchange:unit": "pen" });
    home.type("691");

    expect(home.rows()[0]?.total).toBe("200.00");
  });
});

describe("selling dollars on the served home page", () => {
  it("prices the same amount at the best buying rate and says who pays the least", async () => {
    const home = await openHome();
    home.chooseSide("sell");
    home.type("1,000");

    expect(home.summary("sell")).toBe(
      "You get S/ 3,441.00 at Western Union S/ 11.00 more than at CambiaFX, which pays the least.",
    );
    expect(home.rows("sell")[0]).toMatchObject({
      house: "Western Union",
      total: "3,441.00",
    });
    expect(home.head("sell")).toBe("You get for US$1,000.00");
  });

  it("asks for soles to get when the amount is in soles", async () => {
    const home = await openHome();
    home.chooseSide("sell");
    home.type("1000");
    home.flip();

    expect(home.head("sell")).toContain("to get S/");
    expect(home.summary("sell")).toMatch(/^You sell US\$ [\d.,]+ at Western Union/);
  });

  it("keeps the amount when the side changes", async () => {
    const home = await openHome();
    home.type("350");
    home.chooseSide("sell");

    expect(home.input.value).toBe("350");
    expect(home.figure("sell")).toBe("1,204.35");
  });

  it("tells the seller what is wrong with an amount, as the buyer is told", async () => {
    const home = await openHome();
    home.chooseSide("sell");
    const cases: [string, string, string][] = [
      ["", "", "false"],
      ["0", "Type an amount above zero.", "true"],
      ["12a", "Use digits only, for example 200 or 1,250.50.", "true"],
      ["2000000000", "Type 1,000,000,000 or less.", "true"],
      ["12.5", "S/ 0.14 more than at CambiaFX, which pays the least.", "false"],
    ];

    for (const [typed, said, invalid] of cases) {
      home.type(typed);
      expect(home.note("sell"), typed).toBe(said);
      expect(home.input.getAttribute("aria-invalid"), typed).toBe(invalid);
    }
  });
});

describe("remembering the visitor's choices", () => {
  it("keeps the amount, the unit and the side for the next visit", async () => {
    const home = await openHome();
    home.type("350");
    home.flip();
    home.chooseSide("sell");

    expect(home.win.localStorage.getItem("perexchange:amount")).toBe(home.input.value);
    expect(home.win.localStorage.getItem("perexchange:unit")).toBe("pen");
    expect(home.win.localStorage.getItem("perexchange:side")).toBe("sell");
  });

  it("opens with the amount and the side the visitor left", async () => {
    const home = await openHome({
      "perexchange:amount": "1,000",
      "perexchange:side": "sell",
    });

    expect(home.input.value).toBe("1,000");
    expect(home.summary("sell")).toContain("You get S/ 3,441.00 at Western Union");
    expect(
      (home.win.document.getElementById("side-sell") as unknown as HTMLInputElement)
        .checked,
    ).toBe(true);
    expect(home.fieldLabel()).toBe("Amount to sell");
  });

  it("starts without an amount when the saved one is empty", async () => {
    const home = await openHome({ "perexchange:amount": "" });

    expect(home.reading()).toBe("empty");
    expect(home.summary()).toContain("Best rate per US$1");
  });

  it("still works when the browser refuses storage", async () => {
    const home = await openHome({}, "blocked");
    home.type("300");

    expect(home.figure()).toBe("1,036.50");
    home.flip();
    expect(home.summary()).toContain("You get US$ 300.00");
  });

  it("still calculates when the browser reads storage but refuses to write", async () => {
    const home = await openHome({}, "full");
    home.type("300");

    expect(home.figure()).toBe("1,036.50");
    home.flip();
    expect(home.summary()).toContain("You get US$ 300.00");
    home.flip();
    expect(home.input.value).toBe("300.00");
    home.chooseSide("sell");
    home.type("1,000");
    expect(home.figure("sell")).toBe("3,441.00");
  });
});

describe("the next step from the served home page", () => {
  it("makes the one button lead to the best house's own site", async () => {
    const home = await openHome();
    home.type("200");
    const cta = home.cta();

    expect(cta.getAttribute("href")).toBe("https://cambioselgordito.com/");
    expect(cta.getAttribute("target")).toBe("_blank");
    expect(cta.getAttribute("rel")).toContain("noopener");
    expect(cta.textContent).toContain("Go to Gordito digital");
    expect(home.cta("sell").getAttribute("href")).toBe(
      "https://www.westernunionperu.pe/cambiodemoneda",
    );
  });

  it("makes each row a link to its house, and its details a second link", async () => {
    const home = await openHome();
    const rows = home.rows();
    const details = home
      .results("buy")
      .querySelector('tr[data-house="CambiaFX"] .details-col a');

    expect(rows[1]?.link.getAttribute("href")).toBe("https://cambiafx.pe/");
    expect(rows[1]?.link.getAttribute("target")).toBe("_blank");
    expect(details?.getAttribute("href")).toBe("/house/cambiafx/");
    expect(details?.textContent).toContain("Details");
  });

  it("marks only the house whose rate is older than the rest", async () => {
    const home = await openHome();
    const late = home.rows().filter((row) => row.late !== null);

    expect(late.map((row) => row.house)).toEqual(["Okane"]);
    expect(late[0]?.late).toMatch(/^Rate from \d+ (h|d) ago$/);
  });
});

describe("the best rate history page", () => {
  it("is linked from every page's navigation, and the home page carries no chart", async () => {
    for (const file of ["index.html", "house/cambiafx/index.html", "docs/index.html"]) {
      expect(await page(file, complete), file).toContain('href="/history/"');
    }

    const home = await page("index.html", complete);

    expect(home).not.toContain("chart-block");
    expect(home).not.toContain('<svg class="plot');
  });

  it("opens on the side the visitor left on the rates page, and keeps a new choice", async () => {
    const win = new Window({ url: `${complete.origin}/history/`, width: 1280 });
    win.localStorage.setItem("perexchange:side", "sell");
    win.document.write(await page("history/index.html", complete));
    const doc = win.document as unknown as Document;
    bindSide(doc, storageOf(doc));
    const radio = (side: string) =>
      doc.getElementById(`side-${side}`) as HTMLInputElement;

    expect(radio("sell").checked).toBe(true);
    expect(radio("buy").checked).toBe(false);

    radio("buy").click();

    expect(win.localStorage.getItem("perexchange:side")).toBe("buy");
  });

  it("says how far the best rate moved in words, for each range", async () => {
    const html = await page("history/index.html", complete);
    const buy = html.split('data-side="sell"')[0];
    const figure = (range: string) =>
      text(
        buy.match(
          new RegExp(`<figure id="chart-buy-${range}"[\\s\\S]*?</figure>`),
        )?.[0] ?? "",
      );

    expect(text(buy)).toContain("7 days 30 days All");
    expect(figure("7d")).toContain(
      "Up S/ 0.0050 (0.1%) in 7 days, from S/ 3.4500 to S/ 3.4550.",
    );
    expect(figure("30d")).toContain(
      "Down S/ 0.0100 (0.3%) in 30 days, from S/ 3.4650 to S/ 3.4550.",
    );
    expect(figure("all")).toMatch(
      /Down S\/ 0\.0200 \(0\.6%\) since \d+ \w{3}, from S\/ 3\.4750 to S\/ 3\.4550\./,
    );
  });

  it("charts the cheapest base rate and never a special rate", async () => {
    const html = await page("history/index.html", complete);

    expect(html).not.toContain("3.4000");
    expect(text(html)).toContain("now 3.4550, from 3.4500 to 3.4750");
  });

  it("labels the axis in days and never in minutes", async () => {
    const html = await page("history/index.html", complete);
    const seven = html.match(/<figure id="chart-buy-7d"[\s\S]*?<\/figure>/)?.[0] ?? "";
    const axis = [...seven.matchAll(/<text[^>]*>([^<]*)<\/text>/g)].map((one) =>
      one[1]!.trim(),
    );

    expect(axis.some((label) => /^\d{1,2} [A-Z][a-z]{2}$/.test(label))).toBe(true);
    expect(axis.some((label) => /\d:\d\d/.test(label))).toBe(false);
  });

  it("repeats nothing under the chart", async () => {
    const html = await page("history/index.html", complete);

    expect(text(html)).not.toContain("readings in this range");
  });

  it("has a wide and a narrow drawing of each range", async () => {
    const html = await page("history/index.html", complete);

    expect(html.match(/<svg class="plot wide"/g)).toHaveLength(6);
    expect(html.match(/<svg class="plot narrow"/g)).toHaveLength(6);
  });

  it("shows an empty state, not a line, until two days are recorded", async () => {
    const html = await page("history/index.html");

    expect(
      text(html).match(
        /The chart appears once two days of readings are recorded\. The first is from 8 Oct\./g,
      ),
    ).toHaveLength(2);
    expect(html).not.toContain('<svg class="plot');
    expect(html).not.toContain("chart-block");
  });
});
