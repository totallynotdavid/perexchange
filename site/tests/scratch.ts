import { mkdir, mkdtemp } from "node:fs/promises";
import path from "node:path";

const SCRATCH = path.resolve(import.meta.dirname, "../.scratch");

/**
 * A new empty directory inside the site directory. Astro stages files under
 * `site/.astro` and renames them into the output, and a rename fails across
 * filesystems, which is where the operating system's temporary directory often is.
 */
export async function scratchDir(prefix: string): Promise<string> {
  await mkdir(SCRATCH, { recursive: true });
  return mkdtemp(path.join(SCRATCH, `${prefix}-`));
}
