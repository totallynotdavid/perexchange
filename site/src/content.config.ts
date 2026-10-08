import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";

/** The library's own Markdown, read in place so the site and the repository cannot drift. */
const library = defineCollection({
  loader: glob({
    base: "..",
    pattern: [
      "README.md",
      "docs/api.md",
      "docs/architecture.md",
      "packages/cli/README.md",
    ],
    generateId: ({ entry }) => entry.replace(/\.md$/, ""),
  }),
});

const site = defineCollection({
  loader: glob({ base: "./src/docs", pattern: "*.md" }),
});

export const collections = { library, site };
