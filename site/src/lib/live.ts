import { formatAge } from "./format.ts";
import { isOld, minutesSince } from "./market.ts";

/** Ages come from the server when the page renders. A cached page is older by the time it is read. */
export function refreshAges(root: ParentNode, now = Date.now()): void {
  for (const time of root.querySelectorAll<HTMLTimeElement>("time[data-age]")) {
    const minutes = minutesSince(time.dateTime, now);
    const text = formatAge(minutes);
    if (time.textContent !== text) {
      time.textContent = text;
    }
    time.classList.toggle("old", isOld(minutes));
  }

  for (const notice of root.querySelectorAll<HTMLElement>("[data-since]")) {
    notice.hidden = !isOld(minutesSince(notice.dataset.since ?? "", now));
  }
}

export function keepAgesFresh(): void {
  refreshAges(document);
  setInterval(() => refreshAges(document), 30_000);
}
