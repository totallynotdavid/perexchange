import { describe, expect, it } from "vitest";

import { dataSource } from "../src/lib/data-source.mjs";

const PUBLISHED =
  "https://raw.githubusercontent.com/totallynotdavid/perexchange/data";

describe("the data source", () => {
  it("is the published branch when nothing is set", () => {
    expect(dataSource({}, "/site")).toBe(PUBLISHED);
  });

  it("treats empty variables as unset", () => {
    expect(
      dataSource(
        {
          PEREXCHANGE_DATA: "",
          VERCEL_GIT_REPO_OWNER: "",
          VERCEL_GIT_REPO_SLUG: "",
        },
        "/site",
      ),
    ).toBe(PUBLISHED);
  });

  it("follows the repository Vercel names", () => {
    expect(
      dataSource(
        { VERCEL_GIT_REPO_OWNER: "someone", VERCEL_GIT_REPO_SLUG: "fork" },
        "/site",
      ),
    ).toBe("https://raw.githubusercontent.com/someone/fork/data");
  });

  it("resolves a data directory against the site root", () => {
    expect(dataSource({ PEREXCHANGE_DATA: "data" }, "/site")).toBe(
      "/site/data",
    );
  });
});
