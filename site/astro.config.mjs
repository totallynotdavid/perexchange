import path from "node:path";
import { fileURLToPath } from "node:url";

import node from "@astrojs/node";
import { unified } from "@astrojs/markdown-remark";
import vercel from "@astrojs/vercel";
import { defineConfig } from "astro/config";

import rehypeRepoLinks from "./src/lib/repo-links.mjs";

// Use the published `data` branch unless PEREXCHANGE_DATA names a directory.
// Resolve that directory against this file because a build can run from "/".
const PUBLISHED_DATA = `https://raw.githubusercontent.com/${process.env.VERCEL_GIT_REPO_OWNER ?? "totallynotdavid"}/${process.env.VERCEL_GIT_REPO_SLUG ?? "perexchange"}/data`;
const siteRoot = path.dirname(fileURLToPath(import.meta.url));
const dataSource = process.env.PEREXCHANGE_DATA
  ? path.resolve(siteRoot, process.env.PEREXCHANGE_DATA)
  : PUBLISHED_DATA;

// Vercel sets VERCEL during a build. The rates pages render on request there and are
// cached for one snapshot interval. Anywhere else a Node server runs them.
const adapter = process.env.VERCEL
  ? vercel({ isr: { expiration: 15 * 60 } })
  : node({ mode: "standalone" });

export default defineConfig({
  adapter,
  trailingSlash: "always",
  // The default, "jsx", drops the space where a line break meets an element, which joins words.
  compressHTML: true,
  build: { format: "directory", inlineStylesheets: "never" },
  devToolbar: { enabled: false },
  // The CSP in vercel.json forbids inline scripts, so no script may be inlined.
  vite: {
    build: {
      assetsInlineLimit: 0,
      // Exclude unused imports from the Vercel adapter's entry. Otherwise the function loads
      // rolldown without shipping its native binding.
      rolldownOptions: {
        treeshake: {
          moduleSideEffects: (id) => id !== "rolldown" && id !== "@vercel/routing-utils",
        },
      },
    },
    define: { __DATA_SOURCE__: JSON.stringify(dataSource) },
  },
  markdown: {
    shikiConfig: {
      themes: { light: "github-light-high-contrast", dark: "github-dark" },
      defaultColor: false,
    },
    processor: unified({ rehypePlugins: [rehypeRepoLinks] }),
  },
});
