import path from "node:path";

/**
 * Where the site reads its snapshots: the directory PEREXCHANGE_DATA names, resolved
 * against `siteRoot` because a build can run from "/", or else the published `data`
 * branch. An empty variable counts as unset, so a copied `.env.example` works as is.
 */
export function dataSource(env, siteRoot) {
  if (env.PEREXCHANGE_DATA) {
    return path.resolve(siteRoot, env.PEREXCHANGE_DATA);
  }
  const owner = env.VERCEL_GIT_REPO_OWNER || "totallynotdavid";
  const slug = env.VERCEL_GIT_REPO_SLUG || "perexchange";
  return `https://raw.githubusercontent.com/${owner}/${slug}/data`;
}
