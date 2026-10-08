const LIMA = "America/Lima";

/** Prices carry four decimals, as the library's own output does. */
export function formatPrice(price: number): string {
  return price.toFixed(4);
}

export function formatSpread(buy: number, sell: number): string {
  return (sell - buy).toFixed(4);
}

export function formatAge(minutes: number): string {
  if (minutes < 1) {
    return "now";
  }
  if (minutes < 60) {
    return `${minutes} min`;
  }
  if (minutes < 60 * 48) {
    return `${Math.round(minutes / 60)} h`;
  }
  return `${Math.round(minutes / (60 * 24))} d`;
}

export function formatMoney(amount: number): string {
  return amount.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function formatLimaTime(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", {
    timeZone: LIMA,
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}
