import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";

import { afterAll, describe, expect, it } from "vitest";

import rehypeRepoLinks, { resolveRepoLink } from "../src/lib/repo-links.mjs";
import { scratchDir } from "./scratch.ts";

const root = await scratchDir("repo-links");
await mkdir(path.join(root, "docs"));
await mkdir(path.join(root, "packages/core"), { recursive: true });
await writeFile(path.join(root, "docs/api.md"), "");
const readme = path.join(root, "README.md");
const apiDoc = path.join(root, "docs/api.md");

afterAll(async () => {
  await rm(root, { recursive: true, force: true });
});

const GITHUB = "https://github.com/totallynotdavid/perexchange";

describe("resolveRepoLink", () => {
  it("sends a link to a rendered file to its page, keeping the anchor", () => {
    expect(resolveRepoLink("docs/api.md", readme, root)).toBe("/docs/api/");
    expect(resolveRepoLink("docs/api.md#fetch", readme, root)).toBe("/docs/api/#fetch");
    expect(resolveRepoLink("../README.md", apiDoc, root)).toBe("/docs/");
  });

  it("sends other repository files to GitHub as blobs and folders as trees", () => {
    expect(resolveRepoLink("LICENSE", readme, root)).toBe(
      `${GITHUB}/blob/master/LICENSE`,
    );
    expect(resolveRepoLink("packages/core", readme, root)).toBe(
      `${GITHUB}/tree/master/packages/core`,
    );
  });

  it("leaves absolute links, site paths and anchors alone", () => {
    for (const href of [
      "https://example.com/x",
      "mailto:a@b.c",
      "/docs/api/",
      "#usage",
      "",
    ]) {
      expect(resolveRepoLink(href, readme, root)).toBe(href);
    }
  });
});

describe("rehypeRepoLinks", () => {
  const link = (href: string, ...children: object[]) => ({
    type: "element",
    tagName: "a",
    properties: { href },
    children,
  });
  const image = { type: "element", tagName: "img", properties: {}, children: [] };
  const text = (value: string) => ({ type: "text", value });

  it("drops a row of badges and rewrites the links in prose", () => {
    const badges = {
      type: "element",
      tagName: "p",
      children: [
        link("https://ci.example/badge", image),
        text("\n"),
        link("https://pypi.org/p", image),
      ],
    };
    const prose = {
      type: "element",
      tagName: "p",
      children: [text("See "), link("docs/api.md", text("the API"))],
    };
    const tree = { type: "root", children: [badges, prose] };

    rehypeRepoLinks({ repoRoot: root })(tree, { path: readme });

    expect(tree.children).toEqual([prose]);
    expect(prose.children[1]).toMatchObject({ properties: { href: "/docs/api/" } });
  });

  it("keeps a paragraph that mixes a linked image with words", () => {
    const mixed = {
      type: "element",
      tagName: "p",
      children: [link("https://x.example", image), text(" and some words")],
    };
    const tree = { type: "root", children: [mixed] };

    rehypeRepoLinks({ repoRoot: root })(tree, { path: readme });

    expect(tree.children).toHaveLength(1);
  });
});
