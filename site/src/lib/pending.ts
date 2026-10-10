/** A cancelled navigation (Escape, the stop button) sends no event, so the mark clears itself. */
const GIVE_UP_MS = 15_000;

/** Whether `to` is another page of this site, or this page again, and not a jump within it. */
function isRoundTrip(to: URL, here: Location): boolean {
  if (to.origin !== here.origin) {
    return false;
  }
  const jumpsWithinPage =
    to.hash !== "" && to.pathname === here.pathname && to.search === here.search;
  return !jumpsWithinPage;
}

function clickAsksServer(
  event: MouseEvent,
  anchor: HTMLAnchorElement,
  here: Location,
): boolean {
  if (event.defaultPrevented || event.button !== 0) {
    return false;
  }
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
    return false;
  }
  if (
    (anchor.target !== "" && anchor.target !== "_self") ||
    anchor.hasAttribute("download")
  ) {
    return false;
  }
  return isRoundTrip(new URL(anchor.href, here.href), here);
}

function submitAsksServer(
  event: SubmitEvent,
  form: HTMLFormElement,
  here: Location,
): boolean {
  if (event.defaultPrevented) {
    return false;
  }
  const target = event.submitter?.getAttribute("formtarget") ?? form.target;
  const method = event.submitter?.getAttribute("formmethod") ?? form.method;
  if ((target !== "" && target !== "_self") || method.toLowerCase() === "dialog") {
    return false;
  }
  const action =
    event.submitter?.getAttribute("formaction") ?? form.getAttribute("action") ?? "";
  return isRoundTrip(new URL(action, here.href), here);
}

/**
 * Marks the page `data-pending` from a click on a link or the submit of a form until the next
 * page replaces it, so the stylesheet can show that the server is working. Every page is
 * rendered on request. A submitted form is also marked `aria-busy`.
 */
export function showPendingNavigation(win: Window, doc: Document): void {
  const root = doc.documentElement;
  let giveUp: ReturnType<typeof setTimeout> | undefined;

  const clear = () => {
    clearTimeout(giveUp);
    delete root.dataset.pending;
    for (const form of doc.querySelectorAll("form[aria-busy]")) {
      form.removeAttribute("aria-busy");
    }
  };

  const start = () => {
    root.dataset.pending = "";
    clearTimeout(giveUp);
    giveUp = setTimeout(clear, GIVE_UP_MS);
  };

  doc.addEventListener("click", (event) => {
    const anchor = (event.target as Element | null)?.closest<HTMLAnchorElement>(
      "a[href]",
    );
    if (anchor && clickAsksServer(event, anchor, win.location)) {
      start();
    }
  });

  doc.addEventListener("submit", (event) => {
    const form = event.target as HTMLFormElement;
    if (submitAsksServer(event as SubmitEvent, form, win.location)) {
      form.setAttribute("aria-busy", "true");
      start();
    }
  });

  // Going back can restore this page from memory with the mark still on it.
  win.addEventListener("pageshow", clear);
}
