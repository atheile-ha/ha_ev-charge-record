import type { Session } from "./types";

export type LiveState = "idle" | "candidate" | "charging" | "paused" | "error" | "awaiting_final";

// The live values of the running session, as the server resolves them.
export interface LivePayload {
  state: LiveState;
  active: boolean;
  wallbox: { name: string; max_power_kw: number };
  currency: string;
  session_start: string | null;
  vehicle: { id: string; name: string } | null;
  vehicle_guest: boolean;
  identification_source: string | null;
  identification_decided: boolean;
  location: string | null;
  soc_start: number | null;
  soc: number | null;
  soc_target: number | null;
  charge_end: string | null;
  charge_power_kw: number | null;
  energy_kwh: number | null;
  energy_grid_kwh: number | null;
  energy_solar_kwh: number | null;
  grid_share_pct: number | null;
  cost: number | null;
  effective_price: number | null;
  net_duration_min: number | null;
  plug_duration_min: number | null;
  flagged: boolean;
  charge_error: boolean;
  location_conflict: boolean;
}

const MS_PER_MINUTE = 60_000;

// The charging time keeps running between two pushes while energy is taken up.
export function netDurationMinutes(
  payload: LivePayload,
  receivedAt: number,
  now: number,
): number | null {
  if (payload.net_duration_min === null) {
    return null;
  }
  const running = payload.state === "candidate" || payload.state === "charging";
  return payload.net_duration_min + (running ? (now - receivedAt) / MS_PER_MINUTE : 0);
}

export function plugDurationMinutes(payload: LivePayload, now: number): number | null {
  if (payload.session_start === null) {
    return null;
  }
  return Math.max((now - new Date(payload.session_start).getTime()) / MS_PER_MINUTE, 0);
}

// The share of solar energy in what the session has taken up so far.
export function solarSharePercent(payload: LivePayload): number | null {
  const grid = payload.energy_grid_kwh;
  const solar = payload.energy_solar_kwh;
  if (grid === null || solar === null || grid + solar <= 0) {
    return null;
  }
  return (solar / (grid + solar)) * 100;
}

// The solar share of a month over the sessions that recorded a split. A
// session without one, such as an imported or external session, does not count
// against the share.
export function monthSolarSharePercent(sessions: Session[]): number | null {
  let grid = 0;
  let solar = 0;
  for (const session of sessions) {
    if (session.energy_grid_kwh !== null && session.energy_solar_kwh !== null) {
      grid += session.energy_grid_kwh;
      solar += session.energy_solar_kwh;
    }
  }
  return grid + solar > 0 ? (solar / (grid + solar)) * 100 : null;
}
