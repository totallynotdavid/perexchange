import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

import { parseHistory, parseLatest } from "./data.ts";
import type { History, Latest } from "./data.ts";

/** A directory, or the URL of a published copy of one. astro.config.mjs injects it. */
declare const __DATA_SOURCE__: string;

export const HISTORY_DAYS = 30;

/** Every page render asks for the same files, and the house pages render separately. */
const CACHE_MS = 5 * 60_000;
const cache = new Map<string, { at: number; text: Promise<string | null> }>();

function isUrl(source: string): boolean {
  return /^https?:\/\//.test(source);
}

async function readText(source: string, name: string): Promise<string | null> {
  if (!isUrl(source)) {
    return readFile(path.join(source, name), "utf8").catch(() => null);
  }
  const url = `${source}/${name}`;
  const hit = cache.get(url);
  if (hit && Date.now() - hit.at < CACHE_MS) {
    return hit.text;
  }
  const text = fetch(url).then((response) => {
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      throw new Error(`${url} answered ${response.status}`);
    }
    return response.text();
  });
  cache.set(url, { at: Date.now(), text });
  text.catch(() => cache.delete(url));
  return text;
}

export async function loadLatest(source = __DATA_SOURCE__): Promise<Latest> {
  const text = await readText(source, "latest.json");
  if (text === null) {
    throw new Error(
      `No snapshot at ${source}/latest.json. Run \`bun run data\` to record one, or set PEREXCHANGE_DATA.`,
    );
  }
  return parseLatest(text);
}

/** The most days the best-rate chart reads. Its "All" range ends here. */
export const ALL_DAYS = 365;

/** A published copy has no listing, so days are asked for in batches of this size. */
const BATCH_DAYS = 30;

const dayFile = (now: Date, back: number) =>
  `history/${new Date(now.getTime() - back * 86_400_000).toISOString().slice(0, 10)}.jsonl`;

/**
 * The text of the history files of the last `days` UTC days. A published copy is read
 * newest first, and reading stops at the first batch that holds no file.
 */
async function historyFiles(source: string, now: Date, days: number): Promise<string[]> {
  if (!isUrl(source)) {
    const names = await readdir(path.join(source, "history")).catch(() => []);
    const kept = names
      .filter((name) => name.endsWith(".jsonl"))
      .sort()
      .slice(-days);
    const files = await Promise.all(
      kept.map((name) => readText(source, `history/${name}`)),
    );
    return files.filter((text) => text !== null);
  }

  const found: string[] = [];
  for (let from = 0; from < days; from += BATCH_DAYS) {
    const backs = Array.from(
      { length: Math.min(BATCH_DAYS, days - from) },
      (_, i) => from + i,
    );
    const batch = await Promise.all(
      backs.map((back) => readText(source, dayFile(now, back))),
    );
    const present = batch.filter((text) => text !== null);
    if (present.length === 0) {
      break;
    }
    found.push(...present);
  }
  return found;
}

export async function loadHistory(
  source = __DATA_SOURCE__,
  now = new Date(),
  days = HISTORY_DAYS,
): Promise<History> {
  return parseHistory(await historyFiles(source, now, days));
}
