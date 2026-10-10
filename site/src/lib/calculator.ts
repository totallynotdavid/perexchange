import { buyView, DEFAULT_AMOUNT, readAmount, sellSummary } from "./amount.ts";
import type { Mode, Reading, Row } from "./amount.ts";

const KEYS = {
  side: "perexchange:side",
  mode: "perexchange:mode",
  amount: (name: string) => `perexchange:amount:${name}`,
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

/** An empty field is waiting for a number; any other reading but a good one is a mistake. */
const isRejected = (reading: Reading) =>
  reading.kind !== "ok" && reading.kind !== "empty";

const setText = (element: Element, text: string) => {
  if (element.textContent !== text) {
    element.textContent = text;
  }
};

function bindSell(calc: HTMLElement, store: Store): void {
  const input = query<HTMLInputElement>(calc, "input[type='text']");
  const output = query<HTMLOutputElement>(calc, "output");
  const rate = Number(output.dataset.rate);
  const key = KEYS.amount("sell");

  const update = () => {
    const reading = readAmount(input.value);
    input.setAttribute("aria-invalid", String(isRejected(reading)));
    output.value = sellSummary(reading, rate);
    calc.setAttribute("data-reading", reading.kind);
  };

  input.value = store.getItem(key) ?? "";
  input.addEventListener("input", () => {
    store.setItem(key, input.value);
    update();
  });
  calc.hidden = false;
  update();
}

function bindBuy(panel: Element, calc: HTMLElement, store: Store): void {
  const radios = [...calc.querySelectorAll<HTMLInputElement>("input[name='mode']")];
  const input = query<HTMLInputElement>(calc, "input[type='text']");
  const output = query<HTMLOutputElement>(calc, "output");
  const label = query(calc, "[data-label]");
  const affix = query(calc, "[data-affix]");
  const rows = [...panel.querySelectorAll<HTMLElement>("tr[data-rate]")];
  const table: Row[] = rows.map((row) => ({
    rate: Number(row.dataset.rate),
    house: row.dataset.house ?? "",
  }));
  const mode = (): Mode =>
    radios.find((radio) => radio.checked)?.value === "pen" ? "pen" : "usd";

  const render = () => {
    const current = mode();
    const reading = readAmount(input.value);
    const view = buyView(current, reading, table);

    setText(label, current === "usd" ? "I want to buy" : "I have");
    setText(affix, current === "usd" ? "US$" : "S/");
    input.setAttribute("aria-invalid", String(isRejected(reading)));
    output.value = view.summary;
    panel.setAttribute("data-reading", reading.kind);

    rows.forEach((row, i) => {
      const cell = view.cells[i];
      if (cell !== undefined) {
        setText(query(row, "[data-total]"), cell.total);
        setText(query(row, "[data-edge]"), cell.edge);
      }
    });
    for (const head of panel.querySelectorAll("[data-head='total']"))
      setText(head, view.heads.total);
    for (const note of panel.querySelectorAll("[data-note='total']"))
      setText(note, view.heads.totalNote);
    for (const head of panel.querySelectorAll("[data-head='edge']"))
      setText(head, view.heads.edge);
  };

  const load = () => {
    input.value = store.getItem(KEYS.amount(mode())) || String(DEFAULT_AMOUNT[mode()]);
    render();
  };

  const saved = store.getItem(KEYS.mode);
  for (const radio of radios) {
    radio.checked = radio.value === (saved === "pen" ? "pen" : "usd");
    radio.addEventListener("change", () => {
      store.setItem(KEYS.mode, mode());
      load();
    });
  }
  input.addEventListener("input", () => {
    store.setItem(KEYS.amount(mode()), input.value);
    render();
  });
  calc.hidden = false;
  load();
}

export function bindBoard(doc: Document): void {
  const store = storageOf(doc);

  const saved = store.getItem(KEYS.side);
  for (const input of doc.querySelectorAll<HTMLInputElement>("input[name='side']")) {
    input.checked = input.value === (saved ?? "buy");
    input.addEventListener("change", () => store.setItem(KEYS.side, input.value));
  }

  for (const panel of doc.querySelectorAll(".panel[data-side]")) {
    const calc = panel.querySelector<HTMLElement>(".amount[data-calc]");
    if (calc?.dataset.calc === "buy") {
      bindBuy(panel, calc, store);
    } else if (calc?.dataset.calc === "sell") {
      bindSell(calc, store);
    }
  }
}
