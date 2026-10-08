import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

import { parseHistory, parseLatest } from "./data.ts";
import type { History, Latest } from "./data.ts";

function dataDir(): string {
  return path.resolve(process.env.PEREXCHANGE_DATA ?? "data");
}

export async function loadLatest(dir = dataDir()): Promise<Latest> {
  let text: string;
  try {
    text = await readFile(path.join(dir, "latest.json"), "utf8");
  } catch {
    throw new Error(
      `No snapshot at ${dir}/latest.json. Run \`bun run data\` to record one, or set PEREXCHANGE_DATA.`,
    );
  }
  return parseLatest(text);
}

export async function loadHistory(dir = dataDir()): Promise<History> {
  const historyDir = path.join(dir, "history");
  let names: string[];
  try {
    names = (await readdir(historyDir)).filter((name) => name.endsWith(".jsonl")).sort();
  } catch {
    return { snapshots: [], skippedLines: 0 };
  }
  const files = await Promise.all(
    names.map((name) => readFile(path.join(historyDir, name), "utf8")),
  );
  return parseHistory(files);
}
