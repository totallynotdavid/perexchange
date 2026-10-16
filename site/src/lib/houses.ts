import type { Quote } from "./data.ts";

/** Compare houses across spellings: "Cambio Mundial" and `cambiomundial` are one house. */
export function houseKey(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]/g, "");
}

interface House {
  name: string;
  site: string;
}

const HOUSES: Record<string, House> = {
  cambiafx: { name: "CambiaFX", site: "https://cambiafx.pe/" },
  cambiodigital: { name: "Cambio Digital", site: "https://cambiodigitalperu.com/" },
  cambiomundial: { name: "Cambio Mundial", site: "https://www.cambiomundial.com/" },
  cambioseguro: { name: "Cambio Seguro", site: "https://cambioseguro.com/" },
  cambiosol: { name: "Cambiosol", site: "https://cambiosol.pe/" },
  chapacambio: { name: "Chapa Cambio", site: "https://chapacambio.com/" },
  chaskidolar: { name: "Chaski Dólar", site: "https://chaskidolar.com/" },
  defiperu: { name: "Defi Perú", site: "https://www.defiperu.pe/" },
  dichikash: { name: "Dichikash", site: "https://dichikash.com/" },
  dinekash: { name: "Dinekash", site: "https://dinekash.pe/" },
  dolarex: { name: "Dolarex", site: "https://dolarex.pe/" },
  dollarhouse: { name: "Dollar House", site: "https://dollarhouse.pe/" },
  gorditodigital: { name: "Gordito digital", site: "https://cambioselgordito.com/" },
  inkamoney: { name: "Inka Money", site: "https://inkamoney.com/" },
  inticambio: { name: "Inticambio", site: "https://inticambio.pe/" },
  kambioonline: { name: "Kambio Online", site: "https://kambio.com.pe/" },
  marketdollar: { name: "Market Dollar", site: "https://market-dollar.com/" },
  masscambio: { name: "Mass Cambio", site: "https://cambiosmass.com/" },
  mercadocambiario: {
    name: "Mercado Cambiario",
    site: "https://www.mercadocambiario.pe/",
  },
  metafx: { name: "MetaFX", site: "https://metafxperu.com/" },
  moneyhouse: { name: "Money House", site: "https://moneyhouse.pe/" },
  moneyplus: { name: "Money Plus", site: "https://moneyplus.com.pe/" },
  okane: { name: "Okane", site: "https://okanecambiodigital.com/" },
  srcambio: { name: "SR Cambio", site: "https://srcambio.pe/" },
  tkambio: { name: "TKambio", site: "https://tkambio.com/" },
  tucambista: { name: "Tu Cambista", site: "https://tucambista.pe/" },
  westernunion: {
    name: "Western Union",
    site: "https://www.westernunionperu.pe/cambiodemoneda",
  },
};

export function houseName(text: string): string {
  return HOUSES[houseKey(text)]?.name ?? text;
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

export function quoteHouse(quote: Quote): string {
  return houseName(isVariant(quote) ? quote.source : quote.name);
}

/**
 * Whether two quotes belong to one house. An aggregator lists many houses under one
 * source, so the source alone cannot identify the house.
 */
export function sameHouse(a: Quote, b: Quote): boolean {
  return houseKey(quoteHouse(a)) === houseKey(quoteHouse(b));
}

export function houseSite(quote: Quote): string | null {
  return HOUSES[houseKey(isVariant(quote) ? quote.source : quote.name)]?.site ?? null;
}

/**
 * Where a row or button for a house leads: its own page when this site knows the address,
 * and otherwise the house's page on this site.
 */
export function houseLink(quote: Quote): { href: string; external: boolean } {
  const site = houseSite(quote);
  return site === null
    ? { href: `/house/${quote.id}/`, external: false }
    : { href: site, external: true };
}
