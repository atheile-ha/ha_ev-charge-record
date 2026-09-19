import type { Session, Vehicle } from "./types";

export type ViewId = "overview" | "detail";

export const UNASSIGNED = "__unassigned__";
export const NO_CARD = "__none__";

export interface Filters {
  vehicle: string;
  location: string;
  chargeType: string;
  card: string;
  status: string;
}

export const EMPTY_FILTERS: Filters = {
  vehicle: "",
  location: "",
  chargeType: "",
  card: "",
  status: "",
};

export interface PanelState {
  view: ViewId;
  year: number;
  month: number;
  filters: Filters;
}

export function currentYearMonth(now: Date, timeZone: string): { year: number; month: number } {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "numeric",
  }).formatToParts(now);
  const pick = (type: string): number =>
    Number(parts.find((part) => part.type === type)?.value ?? 0);
  return { year: pick("year"), month: pick("month") };
}

export function defaultState(now: Date, timeZone: string): PanelState {
  return { view: "overview", ...currentYearMonth(now, timeZone), filters: { ...EMPTY_FILTERS } };
}

export function shiftMonth(
  year: number,
  month: number,
  delta: number,
): { year: number; month: number } {
  const index = year * 12 + (month - 1) + delta;
  return { year: Math.floor(index / 12), month: (index % 12) + 1 };
}

const FILTER_PARAMS: [keyof Filters, string][] = [
  ["vehicle", "vehicle"],
  ["location", "location"],
  ["chargeType", "charge_type"],
  ["status", "status"],
];

// The card filter is not written to the URL: card identifiers stay out of it.
export function serializeState(state: PanelState): string {
  const params = new URLSearchParams({ year: String(state.year), month: String(state.month) });
  for (const [key, name] of FILTER_PARAMS) {
    if (state.filters[key] !== "") {
      params.set(name, state.filters[key]);
    }
  }
  return `/${state.view}?${params.toString()}`;
}

export function parseState(path: string, search: string): Partial<PanelState> {
  const result: Partial<PanelState> = {};
  const segment = path.split("/").filter((part) => part !== "")[0];
  if (segment === "overview" || segment === "detail") {
    result.view = segment;
  }
  const params = new URLSearchParams(search);
  const year = Number(params.get("year"));
  const month = Number(params.get("month"));
  if (Number.isInteger(year) && year >= 1000 && year <= 9999 && Number.isInteger(month)) {
    if (month >= 1 && month <= 12) {
      result.year = year;
      result.month = month;
    }
  }
  const filters = { ...EMPTY_FILTERS };
  let hasFilter = false;
  for (const [key, name] of FILTER_PARAMS) {
    const value = params.get(name);
    if (value) {
      filters[key] = value;
      hasFilter = true;
    }
  }
  if (hasFilter) {
    result.filters = filters;
  }
  return result;
}

export function hasActiveFilter(filters: Filters): boolean {
  return Object.values(filters).some((value) => value !== "");
}

export function applyFilters(sessions: Session[], filters: Filters): Session[] {
  return sessions.filter((session) => {
    if (filters.vehicle === UNASSIGNED) {
      if (session.vehicle_id !== null) return false;
    } else if (filters.vehicle !== "" && session.vehicle_id !== filters.vehicle) {
      return false;
    }
    if (filters.location !== "" && session.location !== filters.location) return false;
    if (filters.chargeType !== "" && session.charge_type !== filters.chargeType) return false;
    if (filters.status !== "" && session.status !== filters.status) return false;
    if (filters.card === NO_CARD) {
      if (session.card_uid !== null) return false;
    } else if (filters.card !== "" && session.card_uid !== filters.card) {
      return false;
    }
    return true;
  });
}

export interface Option {
  value: string;
  label: string;
}

// Configured vehicles first, then vehicles that only exist in the sessions
// (removed from the configuration, history kept), under their recorded name.
export function vehicleOptions(vehicles: Vehicle[], sessions: Session[]): Option[] {
  const options = new Map<string, string>();
  for (const vehicle of vehicles) {
    options.set(vehicle.id, vehicle.name);
  }
  for (const session of sessions) {
    if (session.vehicle_id !== null && !options.has(session.vehicle_id)) {
      options.set(session.vehicle_id, session.vehicle_name ?? session.vehicle_id);
    }
  }
  return [...options].map(([value, label]) => ({ value, label }));
}

export function cardOptions(sessions: Session[], selected: string): Option[] {
  const options = new Map<string, string>();
  for (const session of sessions) {
    if (session.card_uid !== null && !options.has(session.card_uid)) {
      options.set(session.card_uid, session.card_label || session.card_uid);
    }
  }
  if (selected !== "" && selected !== NO_CARD && !options.has(selected)) {
    options.set(selected, selected);
  }
  return [...options].map(([value, label]) => ({ value, label }));
}

export function yearOptions(available: number[], current: number, selected: number): number[] {
  return [...new Set([...available, current, selected])].sort((a, b) => b - a);
}
