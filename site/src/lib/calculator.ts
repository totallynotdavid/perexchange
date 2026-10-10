import { answer, flipped, readAmount } from "./amount.ts";
import type { Row, Unit } from "./amount.ts";
import type { Side } from "./market.ts";

const KEYS = {
  side: "perexchange:side",
  unit: "perexchange:unit",
  amount: "perexchange:amount",
};

type Store = Pick<Storage, "getItem" | "setItem">;

/**
 * The page works without storage, as when a browser blocks it. A store that reads but
 * refuses to write keeps what it is given until the page closes, and a failure to read
 * or write never stops a calculation.
 */
function storageOf(doc: Document): Store {
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

function query<T extends Element>(root: ParentNode, selector: string): T {
  const found = root.querySelector<T>(selector);
  if (found === null) {
    throw new Error(`The page has no ${selector}`);
  }
  return found;
}

const setText = (element: Element, text: string) => {
  if (element.textContent !== text) {
    element.textContent = text;
  }
};

interface Panel {
  side: Side;
  hero: HTMLElement;
  rows: HTMLElement[];
  table: Row[];
}

function panelsOf(board: ParentNode): Panel[] {
  return [...board.querySelectorAll<HTMLElement>(".hero[data-side]")].flatMap((hero) => {
    const side = hero.dataset.side === "sell" ? "sell" : "buy";
    const results = board.querySelector(`.results[data-side="${side}"]`);
    if (results === null) {
      return [];
    }
    const rows = [...results.querySelectorAll<HTMLElement>("tr[data-rate]")];
    return [
      {
        side,
        hero,
        rows,
        table: rows.map((row) => ({
          rate: Number(row.dataset.rate),
          house: row.dataset.house ?? "",
        })),
      } satisfies Panel,
    ];
  });
}

/**
 * Binds the amount field, the unit button and the side switch to the hero and the table
 * of each side. One field serves both sides, so the amount survives a change of side.
 */
export function bindBoard(doc: Document): void {
  const board = doc.querySelector<HTMLElement>(".board");
  const calc = board?.querySelector<HTMLElement>(".amount");
  // A page with no rate has no amount to price.
  if (board === null || calc === null || calc === undefined) {
    return;
  }
  const store = storageOf(doc);
  const input = query<HTMLInputElement>(calc, "input[type='text']");
  const label = query(calc, "[data-label]");
  const button = query<HTMLButtonElement>(calc, "[data-unit]");
  const sides = [...board.querySelectorAll<HTMLInputElement>("input[name='side']")];
  const panels = panelsOf(board);

  let unit: Unit = store.getItem(KEYS.unit) === "pen" ? "pen" : "usd";
  const side = (): Side =>
    sides.find((radio) => radio.checked)?.value === "sell" ? "sell" : "buy";

  const render = () => {
    const reading = readAmount(input.value);
    const current = side();
    const soles = unit === "pen";

    setText(label, current === "buy" ? "Amount to buy" : "Amount to sell");
    setText(query(button, "[data-unit-text]"), soles ? "S/" : "US$");
    setText(
      query(button, "[data-unit-hint]"),
      soles ? ", change to dollars" : ", change to soles",
    );
    input.setAttribute(
      "aria-invalid",
      String(reading.kind !== "ok" && reading.kind !== "empty"),
    );
    board.dataset.reading = reading.kind;

    for (const panel of panels) {
      const view = answer(panel.side, unit, reading, panel.table);
      const part = (name: string) => query(panel.hero, `[data-part='${name}']`);
      setText(part("label"), view.label);
      setText(part("currency"), view.currency);
      setText(part("figure"), view.figure);
      setText(part("note"), view.note);

      const results = board.querySelector(`.results[data-side="${panel.side}"]`);
      for (const head of results?.querySelectorAll("[data-head='label']") ?? []) {
        setText(head, view.head.label);
      }
      for (const head of results?.querySelectorAll("[data-head='for']") ?? []) {
        setText(head, view.head.for);
      }
      panel.rows.forEach((row, i) => {
        setText(query(row, "[data-total]"), view.totals[i] ?? "");
      });
    }
  };

  const saved = store.getItem(KEYS.side);
  for (const radio of sides) {
    radio.checked = radio.value === (saved === "sell" ? "sell" : "buy");
    radio.addEventListener("change", () => {
      store.setItem(KEYS.side, side());
      render();
    });
  }

  input.value = store.getItem(KEYS.amount) ?? "";
  input.addEventListener("input", () => {
    store.setItem(KEYS.amount, input.value);
    render();
  });
  button.addEventListener("click", () => {
    const best = panels.find((panel) => panel.side === side())?.table[0]?.rate;
    input.value = flipped(side(), unit, input.value, best);
    unit = unit === "usd" ? "pen" : "usd";
    store.setItem(KEYS.unit, unit);
    store.setItem(KEYS.amount, input.value);
    render();
  });

  // The history is below the answer, so a phone starts with it closed.
  if (doc.defaultView?.matchMedia("(min-width: 40em)").matches === false) {
    for (const history of board.querySelectorAll<HTMLDetailsElement>("details.history")) {
      history.open = false;
    }
  }

  calc.hidden = false;
  render();
  if (doc.activeElement === null || doc.activeElement === doc.body) {
    input.focus({ preventScroll: true });
  }
}
