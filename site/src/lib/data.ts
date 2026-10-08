export interface Quote {
  id: string;
  source: string;
  name: string;
  buy: number;
  sell: number;
  timestamp: string;
}

export interface Failure {
  source: string;
  error_type: string;
  message: string;
}

export interface Latest {
  generated_at: string;
  library_version: string;
  rates: Quote[];
  failures: Failure[];
}

export interface HistoricalPrice {
  buy: number;
  sell: number;
  ageMinutes: number;
}

export interface Snapshot {
  t: number;
  prices: Record<string, HistoricalPrice>;
}

export interface History {
  snapshots: Snapshot[];
  skippedLines: number;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPrice(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function parseQuote(value: unknown): Quote {
  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    typeof value.source !== "string" ||
    typeof value.name !== "string" ||
    typeof value.timestamp !== "string" ||
    Number.isNaN(Date.parse(value.timestamp)) ||
    !isPrice(value.buy) ||
    !isPrice(value.sell)
  ) {
    throw new Error(`latest.json has a malformed rate: ${JSON.stringify(value)}`);
  }
  return {
    id: value.id,
    source: value.source,
    name: value.name,
    buy: value.buy,
    sell: value.sell,
    timestamp: value.timestamp,
  };
}

function parseFailure(value: unknown): Failure {
  if (
    !isRecord(value) ||
    typeof value.source !== "string" ||
    typeof value.error_type !== "string" ||
    typeof value.message !== "string"
  ) {
    throw new Error(`latest.json has a malformed failure: ${JSON.stringify(value)}`);
  }
  return { source: value.source, error_type: value.error_type, message: value.message };
}

export function parseLatest(text: string): Latest {
  const value: unknown = JSON.parse(text);
  if (
    !isRecord(value) ||
    typeof value.generated_at !== "string" ||
    Number.isNaN(Date.parse(value.generated_at)) ||
    typeof value.library_version !== "string" ||
    !Array.isArray(value.rates) ||
    !Array.isArray(value.failures)
  ) {
    throw new Error("latest.json is not a perexchange snapshot");
  }
  return {
    generated_at: value.generated_at,
    library_version: value.library_version,
    rates: value.rates.map(parseQuote),
    failures: value.failures.map(parseFailure),
  };
}

function parseSnapshot(line: string): Snapshot | null {
  let value: unknown;
  try {
    value = JSON.parse(line);
  } catch {
    return null;
  }
  if (!isRecord(value) || typeof value.t !== "string" || !isRecord(value.r)) {
    return null;
  }
  const t = Date.parse(value.t);
  if (Number.isNaN(t)) {
    return null;
  }

  const prices: Record<string, HistoricalPrice> = {};
  for (const [id, entry] of Object.entries(value.r)) {
    if (!Array.isArray(entry) || !isPrice(entry[0]) || !isPrice(entry[1])) {
      return null;
    }
    const age = entry[2];
    prices[id] = {
      buy: entry[0],
      sell: entry[1],
      ageMinutes: typeof age === "number" && age >= 0 ? age : 0,
    };
  }
  return { t, prices };
}

/**
 * Reads the text of any number of day files. A line that is not a complete snapshot is
 * counted and skipped, so one bad line never hides the rest of the history.
 */
export function parseHistory(files: string[]): History {
  const snapshots: Snapshot[] = [];
  let skippedLines = 0;

  for (const text of files) {
    for (const line of text.split("\n")) {
      if (line.trim() === "") {
        continue;
      }
      const snapshot = parseSnapshot(line);
      if (snapshot === null) {
        skippedLines += 1;
      } else {
        snapshots.push(snapshot);
      }
    }
  }

  snapshots.sort((a, b) => a.t - b.t);
  return { snapshots, skippedLines };
}
