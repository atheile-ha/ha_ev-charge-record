import type { HomeAssistant, Session, StatsResponse, Vehicle } from "./types";

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

export function getStats(hass: HomeAssistant, year: number): Promise<StatsResponse> {
  return hass.callWS<StatsResponse>({ type: "ev_charging/sessions/stats", year });
}

export async function listVehicles(hass: HomeAssistant): Promise<Vehicle[]> {
  const result = await hass.callWS<{ vehicles: Vehicle[] }>({
    type: "ev_charging/vehicles/list",
  });
  return result.vehicles;
}
