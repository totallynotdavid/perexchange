import type { APIRoute } from "astro";

import { loadLatest } from "../../lib/load.ts";

export const GET: APIRoute = async () => {
  const latest = await loadLatest();
  return new Response(JSON.stringify(latest, null, 1) + "\n", {
    headers: { "Content-Type": "application/json" },
  });
};
