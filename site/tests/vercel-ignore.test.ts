import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

const { ignoreCommand } = JSON.parse(
  readFileSync(path.resolve(import.meta.dirname, "../vercel.json"), "utf8"),
) as { ignoreCommand: string };

let repo: string;

function git(...args: string[]): string {
  const run = spawnSync("git", args, { cwd: repo, encoding: "utf8" });
  expect(run.status, run.stderr).toBe(0);
  return run.stdout.trim();
}

/** Commit one file change and return the exit code Vercel would read for that push. */
function push(file: string, ref: string): number | null {
  const previous = git("rev-parse", "HEAD");
  mkdirSync(path.dirname(path.join(repo, file)), { recursive: true });
  writeFileSync(path.join(repo, file), String(Math.random()));
  git("add", "--all");
  git("commit", "--message", "change");
  const env = {
    ...process.env,
    VERCEL_GIT_COMMIT_REF: ref,
    VERCEL_GIT_PREVIOUS_SHA: previous,
  };
  return spawnSync("sh", ["-c", ignoreCommand], { cwd: path.join(repo, "site"), env })
    .status;
}

beforeAll(() => {
  repo = mkdtempSync(path.join(tmpdir(), "vercel-ignore-"));
  git("init", "--quiet", "--initial-branch", "master");
  git("config", "user.name", "test");
  git("config", "user.email", "test@example.com");
  for (const file of ["site/a", "docs/a", "README.md", "other/a"]) {
    mkdirSync(path.dirname(path.join(repo, file)), { recursive: true });
    writeFileSync(path.join(repo, file), "");
  }
  git("add", "--all");
  git("commit", "--message", "start");
});

afterAll(() => {
  rmSync(repo, { recursive: true, force: true });
});

// Vercel skips the build when the command exits 0 and builds when it exits 1.
describe("the ignoreCommand in vercel.json", () => {
  it("builds a push to master that changes the site, its lockfile or the docs it renders", () => {
    expect(push("site/src/page.astro", "master")).toBe(1);
    expect(push("site/bun.lock", "master")).toBe(1);
    expect(push("docs/api.md", "master")).toBe(1);
    expect(push("README.md", "master")).toBe(1);
  });

  it("skips a push to master that changes nothing the site reads", () => {
    expect(push("other/b", "master")).toBe(0);
  });

  it("skips every push to the data branch, even one that changes the site", () => {
    expect(push("site/src/page.astro", "data")).toBe(0);
    expect(push("history/2026-10-09.jsonl", "data")).toBe(0);
  });
});
