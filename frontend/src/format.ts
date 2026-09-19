const EMPTY = "–";

function number(value: number, locale: string, digits: number): string {
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

// A tilde marks a value that is estimated rather than measured.
export function formatEnergy(kwh: number | null, locale: string, estimate = false): string {
  if (kwh === null) {
    return EMPTY;
  }
  return `${estimate ? "~" : ""}${number(kwh, locale, 3)} kWh`;
}

export function formatEnergyWhole(kwh: number | null, locale: string, estimate = false): string {
  if (kwh === null) {
    return EMPTY;
  }
  return `${estimate ? "~" : ""}${number(kwh, locale, 0)} kWh`;
}

export function formatCostWhole(value: number | null, locale: string, currency: string): string {
  if (value === null) {
    return EMPTY;
  }
  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${number(value, locale, 0)} ${currency}`;
  }
}

// Whole hours; below an hour the minutes stay, so a short month does not read as zero.
export function formatDurationWhole(minutes: number | null): string {
  if (minutes === null) {
    return EMPTY;
  }
  const total = Math.round(minutes);
  return total < 60 ? `${total} min` : `${Math.round(total / 60)} h`;
}

export function formatCost(value: number | null, locale: string, currency: string): string {
  if (value === null) {
    return EMPTY;
  }
  try {
    return new Intl.NumberFormat(locale, { style: "currency", currency }).format(value);
  } catch {
    return `${number(value, locale, 2)} ${currency}`;
  }
}

// A price per kWh needs more digits than an amount: 0.1443, not 0.14.
export function formatPricePerKwh(value: number | null, locale: string, currency: string): string {
  if (value === null) {
    return EMPTY;
  }
  try {
    return `${new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      minimumFractionDigits: 3,
      maximumFractionDigits: 4,
    }).format(value)} / kWh`;
  } catch {
    return `${number(value, locale, 4)} ${currency} / kWh`;
  }
}

export function formatDuration(minutes: number | null): string {
  if (minutes === null) {
    return EMPTY;
  }
  const total = Math.round(minutes);
  if (total < 60) {
    return `${total} min`;
  }
  const hours = Math.floor(total / 60);
  const rest = String(total % 60).padStart(2, "0");
  return `${hours}:${rest} h`;
}

export function formatPercent(value: number | null, locale: string): string {
  return value === null ? EMPTY : `${number(value, locale, 0)} %`;
}

export function formatDistance(km: number | null, locale: string): string {
  return km === null ? EMPTY : `${number(km, locale, 0)} km`;
}

export function formatPower(kw: number | null, locale: string): string {
  return kw === null ? EMPTY : `${number(kw, locale, 1)} kW`;
}

export function formatDateTime(iso: string | null, locale: string, timeZone: string): string {
  if (iso === null) {
    return EMPTY;
  }
  return new Intl.DateTimeFormat(locale, {
    weekday: "short",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  }).format(new Date(iso));
}

export function formatTime(iso: string | null, locale: string, timeZone: string): string {
  if (iso === null) {
    return EMPTY;
  }
  return new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  }).format(new Date(iso));
}

export function monthName(month: number, locale: string, style: "long" | "short"): string {
  return new Intl.DateTimeFormat(locale, { month: style, timeZone: "UTC" }).format(
    new Date(Date.UTC(2026, month - 1, 1)),
  );
}

export { EMPTY };
