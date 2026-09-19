import type { HomeAssistant, Session, Vehicle } from "./types";

export interface ListParams {
  year?: number;
  month?: number;
  limit?: number;
}

export async function listSessions(hass: HomeAssistant, params: ListParams): Promise<Session[]> {
  const result = await hass.callWS<{ sessions: Session[] }>({
    type: "ev_charging/sessions/list",
    ...params,
  });
  return result.sessions;
}

export interface YearSessions {
  sessions: Session[];
  years: number[];
}

// All sessions of a year and the years that hold data.
export function listYear(hass: HomeAssistant, year: number): Promise<YearSessions> {
  return hass.callWS<YearSessions>({ type: "ev_charging/sessions/list", year });
}

export async function listVehicles(hass: HomeAssistant): Promise<Vehicle[]> {
  const result = await hass.callWS<{ vehicles: Vehicle[] }>({
    type: "ev_charging/vehicles/list",
  });
  return result.vehicles;
}
