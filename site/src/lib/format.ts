const LIMA = "America/Lima";

/** Prices carry four decimals, as the library's own output does. */
export function formatPrice(price: number): string {
  return price.toFixed(4);
}

/** Formats elapsed minutes for a relative timestamp. */
export function formatAge(minutes: number): string {
  if (minutes < 1) {
    return "just now";
  }
  if (minutes < 60) {
    return `${minutes} min ago`;
  }
  if (minutes < 60 * 48) {
    return `${Math.round(minutes / 60)} h ago`;
  }
  return `${Math.round(minutes / (60 * 24))} d ago`;
}

/** Formats an instant as a Lima calendar day. */
export function formatDay(time: number): string {
  return new Date(time).toLocaleDateString("en-GB", {
    timeZone: LIMA,
    day: "numeric",
    month: "short",
  });
}

export function formatMoney(amount: number): string {
  return amount.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/** Formats an instant as a Lima time for a relative-age tooltip. */
export function formatLimaTime(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", {
    timeZone: LIMA,
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}
