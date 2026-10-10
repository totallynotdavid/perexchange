import type { Quote } from "./data.ts";

/** Compare houses across spellings: "Cambio Mundial" and `cambiomundial` are one house. */
export function houseKey(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]/g, "");
}

const NAMES: Record<string, string> = {
  cambiafx: "CambiaFX",
  cambiomundial: "Cambio Mundial",
  cambioseguro: "Cambio Seguro",
  cambiosol: "Cambiosol",
  chapacambio: "Chapa Cambio",
  chaskidolar: "Chaski Dólar",
  defiperu: "Defi Perú",
  dichikash: "Dichikash",
  dinekash: "Dinekash",
  dolarex: "Dolarex",
  dollarhouse: "Dollar House",
  inkamoney: "Inka Money",
  inticambio: "Inticambio",
  kambioonline: "Kambio Online",
  marketdollar: "Market Dollar",
  masscambio: "Mass Cambio",
  mercadocambiario: "Mercado Cambiario",
  metafx: "MetaFX",
  moneyhouse: "Money House",
  moneyplus: "Money Plus",
  okane: "Okane",
  srcambio: "SR Cambio",
  tkambio: "TKambio",
  tucambista: "Tu Cambista",
  westernunion: "Western Union",
};

/** The name a person knows a house by, from a source id or the name an aggregator lists. */
export function houseName(text: string): string {
  return NAMES[houseKey(text)] ?? text;
}

/**
 * A house that publishes more than one rate has one rate for everyone and others for
 * special cases, such as large amounts. The first, whose id is the source, is the house's
 * rate. The others have the source and a suffix in their id.
 */
export function isVariant(quote: Quote): boolean {
  return quote.id.startsWith(`${quote.source}-`);
}

/** What sets a variant apart, from the suffix of its name: "from US$5,000" or "comparative". */
export function variantLabel(quote: Quote): string {
  const suffix = quote.name.slice(quote.source.length).replace(/^[_\s-]+/, "");
  const amount = Number(suffix);
  return Number.isFinite(amount) && amount > 0
    ? `from US$${amount.toLocaleString("en-US")}`
    : suffix;
}

/** The house a quote belongs to: the one a variant is a variant of, or the quote's own. */
export function quoteHouse(quote: Quote): string {
  return houseName(isVariant(quote) ? quote.source : quote.name);
}
