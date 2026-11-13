import path from "node:path";
import { fileURLToPath } from "node:url";

import node from "@astrojs/node";
import { unified } from "@astrojs/markdown-remark";
import vercel from "@astrojs/vercel";
import { defineConfig } from "astro/config";

import { dataSource } from "./src/lib/data-source.mjs";
import rehypeRepoLinks from "./src/lib/repo-links.mjs";

const siteRoot = path.dirname(fileURLToPath(import.meta.url));

// Vercel sets VERCEL during a build. The rates pages render on request there, and
// vercel.json sets how long the CDN keeps them. ISR is off because it serves an
// expired page before it renders a new one, so a page nobody opened for a day
// shows day-old rates. Anywhere else a Node server runs them.
const adapter = process.env.VERCEL ? vercel() : node({ mode: "standalone" });

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
          moduleSideEffects: (id) =>
            id !== "rolldown" && id !== "@vercel/routing-utils",
        },
      },
    },
    define: {
      __DATA_SOURCE__: JSON.stringify(dataSource(process.env, siteRoot)),
    },
  },
  markdown: {
    shikiConfig: {
      themes: { light: "github-light-high-contrast", dark: "github-dark" },
      defaultColor: false,
    },
    processor: unified({ rehypePlugins: [rehypeRepoLinks] }),
  },
});
