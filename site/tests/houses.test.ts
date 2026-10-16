import { describe, expect, it } from "vitest";

import type { Quote } from "../src/lib/data.ts";
import { sameHouse } from "../src/lib/houses.ts";

function quote(id: string, source: string, name: string): Quote {
  return { id, source, name, buy: 3.4, sell: 3.45, timestamp: "2026-10-08T14:30:00Z" };
}

describe("sameHouse", () => {
  it("is false for two houses an aggregator lists under one source", () => {
    const mundial = quote("cambio-mundial", "cuantoestaeldolar", "Cambio Mundial");
    const digital = quote("cambio-digital", "cuantoestaeldolar", "Cambio Digital");

    expect(sameHouse(mundial, digital)).toBe(false);
  });

  it("is true for a house's own rate and its special rate", () => {
    const own = quote("tkambio", "tkambio", "tkambio");
    const large = quote("tkambio-tkambio_5000", "tkambio", "tkambio_5000");

    expect(sameHouse(own, large)).toBe(true);
  });

  it("is true for one house named two ways by two sources", () => {
    const direct = quote("cambiomundial", "cambiomundial", "cambiomundial");
    const listed = quote("cambio-mundial", "cuantoestaeldolar", "Cambio Mundial");

    expect(sameHouse(direct, listed)).toBe(true);
  });
});
