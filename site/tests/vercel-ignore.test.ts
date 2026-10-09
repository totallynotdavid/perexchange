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

/** The exit code Vercel would read for a push of HEAD, with the given previous SHA. */
function ignore(ref: string, previous: string | undefined): number | null {
  const env: NodeJS.ProcessEnv = { ...process.env, VERCEL_GIT_COMMIT_REF: ref };
  if (previous === undefined) {
    delete env.VERCEL_GIT_PREVIOUS_SHA;
  } else {
    env.VERCEL_GIT_PREVIOUS_SHA = previous;
  }
  return spawnSync("sh", ["-c", ignoreCommand], { cwd: path.join(repo, "site"), env })
    .status;
}

/** Commit one file change and return the exit code Vercel would read for that push. */
function push(file: string, ref: string): number | null {
  const previous = git("rev-parse", "HEAD");
  mkdirSync(path.dirname(path.join(repo, file)), { recursive: true });
  writeFileSync(path.join(repo, file), String(Math.random()));
  git("add", "--all");
  git("commit", "--message", "change");
  return ignore(ref, previous);
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

  // Vercel reads any exit code other than 0 and 1 as a failed command, not a build.
  it("builds, and does not fail, when the previous commit is gone from the clone", () => {
    const gone = "047eb4dea315264dd8c2f67f5799118a219d4e0b";

    expect(ignore("master", gone)).toBe(1);
    expect(ignore("master", "not-a-commit")).toBe(1);
  });

  it("compares with the parent commit when Vercel gives no previous SHA", () => {
    push("other/c", "master");
    expect(ignore("master", undefined)).toBe(0);
    push("site/src/page.astro", "master");
    expect(ignore("master", undefined)).toBe(1);
  });

  it("builds a first commit, which has no parent", () => {
    const first = spawnSync("git", ["rev-list", "--max-parents=0", "HEAD"], {
      cwd: repo,
      encoding: "utf8",
    }).stdout.trim();
    git("checkout", "--quiet", first);

    expect(ignore("master", undefined)).toBe(1);
    git("checkout", "--quiet", "master");
  });
});
