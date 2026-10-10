import { Window } from "happy-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { showPendingNavigation } from "../src/lib/pending.ts";

const HERE = "https://perexchange.test/house/cambiafx/";

/** A real DOM holding a page that has run `showPendingNavigation`. */
function openPage(body: string) {
  const win = new Window({
    url: HERE,
    settings: { navigation: { disableMainFrameNavigation: true } },
  });
  win.document.body.innerHTML = body;
  showPendingNavigation(
    win as unknown as globalThis.Window,
    win.document as unknown as Document,
  );
  return {
    win,
    root: win.document.documentElement,
    $: (selector: string) => win.document.querySelector(selector)!,
    pending: () => win.document.documentElement.hasAttribute("data-pending"),
    click(selector: string, init: MouseEventInit = {}) {
      const event = new win.MouseEvent("click", {
        bubbles: true,
        cancelable: true,
        ...init,
      });
      win.document.querySelector(selector)!.dispatchEvent(event);
    },
    /** The browser restoring this page from memory, as Back does. */
    comeBack: () =>
      win.dispatchEvent(new win.PageTransitionEvent("pageshow", { persisted: true })),
  };
}

const LINKS = `
  <header><a id="home" href="/"><span id="brand">perexchange</span></a></header>
  <a id="docs" href="/docs/">Docs</a>
  <a id="reload" href="">Try again</a>
  <a id="jump" href="#chart-7d">7 days</a>
  <a id="other-site" href="https://github.com/totallynotdavid/perexchange">GitHub</a>
  <a id="new-tab" href="/docs/" target="_blank">Docs</a>
  <a id="download" href="/data.csv" download>Data</a>
  <p id="text">No link here</p>
`;

describe("showPendingNavigation on a click", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it.each([
    ["a link to another page of the site", "#docs"],
    ["a link that asks for this page again", "#reload"],
    ["an element inside a link", "#brand"],
  ])("marks the page for %s", (_name, selector) => {
    const page = openPage(LINKS);

    page.click(selector);

    expect(page.pending()).toBe(true);
  });

  it.each([
    ["a link to another site", "#other-site", {}],
    ["a jump within the page", "#jump", {}],
    ["a link that opens a new tab", "#new-tab", {}],
    ["a download", "#download", {}],
    ["text that is not a link", "#text", {}],
    ["a click with the command key", "#docs", { metaKey: true }],
    ["a click with the control key", "#docs", { ctrlKey: true }],
    ["a click with the shift key", "#docs", { shiftKey: true }],
    ["a click that is not the main button", "#docs", { button: 1 }],
  ])("leaves the page alone for %s", (_name, selector, init) => {
    const page = openPage(LINKS);

    page.click(selector, init);

    expect(page.pending()).toBe(false);
  });

  it("leaves the page alone when another script already handled the click", () => {
    const page = openPage(LINKS);
    // A listener on the link runs before the one on the document.
    page.$("#docs").addEventListener("click", (event) => event.preventDefault());

    page.click("#docs");

    expect(page.pending()).toBe(false);
  });

  it("clears the mark when the page comes back from memory", () => {
    const page = openPage(LINKS);
    page.click("#docs");

    page.comeBack();

    expect(page.pending()).toBe(false);
  });

  it("clears the mark when the navigation never arrives", () => {
    const page = openPage(LINKS);
    page.click("#docs");

    vi.advanceTimersByTime(14_999);
    expect(page.pending()).toBe(true);
    vi.advanceTimersByTime(1);

    expect(page.pending()).toBe(false);
  });

  it("restarts the wait when a second link is clicked", () => {
    const page = openPage(LINKS);
    page.click("#docs");
    vi.advanceTimersByTime(10_000);

    page.click("#home");
    vi.advanceTimersByTime(10_000);

    expect(page.pending()).toBe(true);
  });
});

const FORMS = `
  <form id="same-site" action="/search/" method="get"><button id="go">Go</button></form>
  <form id="here"><button>Go</button></form>
  <form id="other-site" action="https://example.com/search" method="post"><button>Go</button></form>
  <form id="new-tab" action="/search/" target="_blank"><button>Go</button></form>
  <form id="dialog" method="dialog"><button>Close</button></form>
  <form id="override" action="/search/">
    <button id="to-other-site" formaction="https://example.com/search">Elsewhere</button>
  </form>
`;

describe("showPendingNavigation on a submit", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  function submit(
    page: ReturnType<typeof openPage>,
    selector: string,
    submitter?: string,
  ) {
    const form = page.$(selector) as unknown as {
      requestSubmit(submitter?: unknown): void;
    };
    form.requestSubmit(submitter ? page.$(submitter) : undefined);
  }

  it.each([
    ["a form that sends to a page of the site", "#same-site"],
    ["a form with no action, which sends to this page", "#here"],
  ])("marks the page and the form busy for %s", (_name, selector) => {
    const page = openPage(FORMS);

    submit(page, selector);

    expect([page.pending(), page.$(selector).getAttribute("aria-busy")]).toEqual([
      true,
      "true",
    ]);
  });

  it.each([
    ["a form that sends to another site", "#other-site"],
    ["a form that opens a new tab", "#new-tab"],
    ["a dialog form", "#dialog"],
  ])("leaves the page alone for %s", (_name, selector) => {
    const page = openPage(FORMS);

    submit(page, selector);

    expect(page.pending()).toBe(false);
  });

  it("follows the button's own action over the form's", () => {
    const page = openPage(FORMS);

    submit(page, "#override", "#to-other-site");

    expect(page.pending()).toBe(false);
  });

  it("leaves the page alone when another script already handled the submit", () => {
    const page = openPage(FORMS);
    page.$("#same-site").addEventListener("submit", (event) => event.preventDefault());

    submit(page, "#same-site");

    expect(page.pending()).toBe(false);
  });

  it("clears the mark and the busy form when the page comes back from memory", () => {
    const page = openPage(FORMS);
    submit(page, "#same-site");

    page.comeBack();

    expect([page.pending(), page.$("#same-site").hasAttribute("aria-busy")]).toEqual([
      false,
      false,
    ]);
  });
});
