/** The URL slug of each library file the site renders. The overview has no slug. */
export const LIBRARY_SLUGS: Record<string, string | undefined> = {
  README: undefined,
  "docs/api": "api",
  "packages/cli/README": "cli",
  "docs/architecture": "architecture",
};

export const DOCS_NAV: { slug: string | undefined; label: string }[] = [
  { slug: undefined, label: "Get started" },
  { slug: "api", label: "API reference" },
  { slug: "cli", label: "CLI" },
  { slug: "architecture", label: "Architecture" },
  { slug: "data", label: "Open data" },
];
