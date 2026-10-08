import { unified } from "@astrojs/markdown-remark";
import { defineConfig } from "astro/config";

import rehypeRepoLinks from "./src/lib/repo-links.mjs";

export default defineConfig({
  trailingSlash: "always",
  // The default, "jsx", drops the space where a line break meets an element, which joins words.
  compressHTML: true,
  build: { format: "directory", inlineStylesheets: "never" },
  devToolbar: { enabled: false },
  // The CSP in public/_headers forbids inline scripts, so no script may be inlined.
  vite: { build: { assetsInlineLimit: 0 } },
  markdown: {
    shikiConfig: {
      themes: { light: "github-light-high-contrast", dark: "github-dark" },
      defaultColor: false,
    },
    processor: unified({ rehypePlugins: [rehypeRepoLinks] }),
  },
});
