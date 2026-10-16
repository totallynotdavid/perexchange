import type { Side } from "./market.ts";

export const KEYS = {
  side: "perexchange:side",
  unit: "perexchange:unit",
  amount: "perexchange:amount",
};

export type Store = Pick<Storage, "getItem" | "setItem">;

/**
 * The page works without storage, as when a browser blocks it. A store that reads but
 * refuses to write keeps what it is given until the page closes, and a failure to read
 * or write never stops a calculation.
 */
export function storageOf(doc: Document): Store {
  const kept = new Map<string, string>();
  const storage = (() => {
    try {
      return doc.defaultView?.localStorage ?? null;
    } catch {
      return null;
    }
  })();
  return {
    getItem: (key) => {
      try {
        return kept.get(key) ?? storage?.getItem(key) ?? null;
      } catch {
        return null;
      }
    },
    setItem: (key, value) => {
      kept.set(key, value);
      try {
        storage?.setItem(key, value);
      } catch {
        // The value stays in `kept` for this page.
      }
    },
  };
}

/**
 * Checks the side the visitor chose last, and keeps a later choice. Every page with a
 * side switch shares the choice, so the history opens on the side the rates left off.
 */
export function bindSide(
  doc: Document,
  store: Store,
  onChange: () => void = () => {},
): { current: () => Side } {
  const radios = [
    ...doc.querySelectorAll<HTMLInputElement>("input[name='side']"),
  ];
  const current = (): Side =>
    radios.find((radio) => radio.checked)?.value === "sell" ? "sell" : "buy";
  const saved = store.getItem(KEYS.side);
  for (const radio of radios) {
    radio.checked = radio.value === (saved === "sell" ? "sell" : "buy");
    radio.addEventListener("change", () => {
      store.setItem(KEYS.side, current());
      onChange();
    });
  }
  return { current };
}
