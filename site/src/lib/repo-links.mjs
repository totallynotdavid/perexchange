import { statSync } from "node:fs";
import path from "node:path";

const REPOSITORY = "https://github.com/totallynotdavid/perexchange";
const BRANCH = "master";
const REPO_ROOT = path.resolve(process.cwd(), "..");

/** Repository files the site renders, and the page that shows each. */
export const PAGES = {
  "README.md": "/docs/",
  "docs/README.md": "/docs/",
  "docs/api.md": "/docs/api/",
  "docs/architecture.md": "/docs/architecture/",
  "packages/cli/README.md": "/docs/cli/",
};

/**
 * Turns a link written for the repository into one that works on the site. A link to
 * a file the site renders goes to its page. Any other link into the repository goes to
 * GitHub. Absolute links and in-page anchors stay as they are.
 */
export function resolveRepoLink(href, fromFile, repoRoot = REPO_ROOT) {
  if (
    href === "" ||
    href.startsWith("#") ||
    /^[a-z][a-z0-9+.-]*:/i.test(href) ||
    href.startsWith("/")
  ) {
    return href;
  }

  const [target, hash = ""] = href.split("#");
  const absolute = path.resolve(path.dirname(fromFile), target);
  const relative = path.relative(repoRoot, absolute).split(path.sep).join("/");
  const suffix = hash === "" ? "" : `#${hash}`;

  if (relative in PAGES) {
    return PAGES[relative] + suffix;
  }
  const kind = isDirectory(absolute) ? "tree" : "blob";
  return `${REPOSITORY}/${kind}/${BRANCH}/${relative}${suffix}`;
}

function isDirectory(location) {
  try {
    return statSync(location).isDirectory();
  } catch {
    return false;
  }
}

function isBadgeParagraph(node) {
  if (node.tagName !== "p") {
    return false;
  }
  const links = node.children.filter((child) => child.type === "element");
  return (
    links.length > 0 &&
    links.every(
      (link) => link.tagName === "a" && link.children.some((c) => c.tagName === "img"),
    ) &&
    node.children.every((child) => child.type === "element" || child.value.trim() === "")
  );
}

function rewrite(node, fromFile, repoRoot) {
  if (!node.children) {
    return;
  }
  node.children = node.children.filter((child) => !isBadgeParagraph(child));
  for (const child of node.children) {
    if (
      child.type === "element" &&
      child.tagName === "a" &&
      typeof child.properties?.href === "string"
    ) {
      child.properties.href = resolveRepoLink(child.properties.href, fromFile, repoRoot);
    }
    rewrite(child, fromFile, repoRoot);
  }
}

export default function rehypeRepoLinks({ repoRoot = REPO_ROOT } = {}) {
  return (tree, file) => {
    if (file.path) {
      rewrite(tree, file.path, repoRoot);
    }
  };
}
