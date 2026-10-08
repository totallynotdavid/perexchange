import { describe, expect, it } from "vitest";

import { bestQuote, convert, parseAmount } from "../src/lib/convert.ts";
import { quote } from "./fixtures.ts";

describe("convert", () => {
  const house = quote("a", 3.4, 3.45);

  it("pays the buy price per dollar when you sell dollars", () => {
    expect(convert(1000, "sell-usd", house)).toBe(3400);
  });

  it("charges the sell price per dollar when you buy dollars", () => {
    expect(convert(3450, "buy-usd", house)).toBe(1000);
  });

  it("rounds to cents", () => {
    expect(convert(100, "buy-usd", house)).toBe(28.99);
    expect(convert(0.01, "sell-usd", quote("b", 3.4333, 3.5))).toBe(0.03);
  });
});

describe("bestQuote", () => {
  const quotes = [quote("a", 3.4, 3.46), quote("b", 3.42, 3.5), quote("c", 3.39, 3.44)];

  it("gives the highest buy price to someone selling dollars", () => {
    expect(bestQuote(quotes, "sell-usd")?.id).toBe("b");
  });

  it("gives the lowest sell price to someone buying dollars", () => {
    expect(bestQuote(quotes, "buy-usd")?.id).toBe("c");
  });

  it("has no best of nothing", () => {
    expect(bestQuote([], "buy-usd")).toBeNull();
  });
});

describe("parseAmount", () => {
  it.each([
    ["250", 250],
    ["1,250.50", 1250.5],
    [" 1 000 ", 1000],
    [".5", 0.5],
    ["10.", 10],
  ])("reads %j as %d", (text, amount) => {
    expect(parseAmount(text)).toBe(amount);
  });

  it.each(["", "abc", "-5", "0", "1.2.3", "1e3", "Infinity", "12abc"])(
    "rejects %j",
    (text) => {
      expect(parseAmount(text)).toBeNull();
    },
  );
});
