import { existsSync, readFileSync } from "node:fs";

const file = "site/data/latest.json";
if (existsSync(file)) {
  const latest = JSON.parse(readFileSync(file, "utf8")) as {
    failures: { source: string }[];
  };
  const names = latest.failures.map((failure) => failure.source);
  if (names.length > 0) {
    console.log(
      `::warning title=Sources did not answer::${names.join(", ")}. If this runner address is blocked, set the REFRESH_RUNNER variable to a runner on another network.`,
    );
  }
}
