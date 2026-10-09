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

/** The history files of the last `HISTORY_DAYS` UTC days. */
async function historyNames(source: string, now: Date): Promise<string[]> {
  if (isUrl(source)) {
    return Array.from({ length: HISTORY_DAYS }, (_, back) => {
      const day = new Date(now.getTime() - back * 86_400_000);
      return `history/${day.toISOString().slice(0, 10)}.jsonl`;
    });
  }
  const names = await readdir(path.join(source, "history")).catch(() => []);
  return names
    .filter((name) => name.endsWith(".jsonl"))
    .sort()
    .slice(-HISTORY_DAYS)
    .map((name) => `history/${name}`);
}

export async function loadHistory(
  source = __DATA_SOURCE__,
  now = new Date(),
): Promise<History> {
  const names = await historyNames(source, now);
  const files = await Promise.all(names.map((name) => readText(source, name)));
  return parseHistory(files.filter((text) => text !== null));
}
