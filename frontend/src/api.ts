import type {
  ChargeType,
  HomeAssistant,
  MergeResult,
  Session,
  SessionLocation,
  Vehicle,
} from "./types";

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

// Sessions that still wait for values, across all years (10, 15).
export async function listOpenSessions(hass: HomeAssistant): Promise<Session[]> {
  const result = await hass.callWS<{ sessions: Session[] }>({ type: "ev_charging/sessions/open" });
  return result.sessions;
}

export interface SessionUpdate {
  soc_start?: number;
  soc_end?: number;
  odometer_km?: number;
  energy_billed_kwh?: number;
  cost?: number;
  charge_type?: ChargeType;
  address?: string;
  note?: string;
  provider?: string;
  plug_end?: string;
}

// A nacherfassung or correction of an already stored session (10, 13, 15).
export async function updateSession(
  hass: HomeAssistant,
  sessionId: string,
  values: SessionUpdate,
): Promise<Session> {
  const result = await hass.callWS<{ session: Session }>({
    type: "ev_charging/sessions/update",
    session_id: sessionId,
    ...values,
  });
  return result.session;
}

export async function deleteSession(hass: HomeAssistant, sessionId: string): Promise<void> {
  await hass.callWS({ type: "ev_charging/sessions/delete", session_id: sessionId });
}

// Accepts a session's remaining missing values as final (10).
export async function closeFollowup(hass: HomeAssistant, sessionId: string): Promise<Session> {
  const result = await hass.callWS<{ session: Session }>({
    type: "ev_charging/sessions/close_followup",
    session_id: sessionId,
  });
  return result.session;
}

// Reassigns a stored session to a different vehicle, or resolves an
// unresolved one, over the same path (7.8).
export async function correctVehicle(
  hass: HomeAssistant,
  sessionId: string,
  vehicleId: string,
): Promise<Session> {
  const result = await hass.callWS<{ session: Session }>({
    type: "ev_charging/sessions/correct_vehicle",
    session_id: sessionId,
    vehicle_id: vehicleId,
  });
  return result.session;
}

export interface SessionCreate {
  location: SessionLocation;
  plug_start: string;
  plug_end: string;
  vehicle_id?: string;
  soc_start?: number;
  soc_end?: number;
  odometer_km?: number;
  energy_billed_kwh?: number;
  charge_type?: ChargeType;
  cost?: number;
  address?: string;
  note?: string;
  provider?: string;
}

// A full manual re-entry of a past charging session (13).
export async function createSession(
  hass: HomeAssistant,
  fields: SessionCreate,
): Promise<Session> {
  const result = await hass.callWS<{ session: Session }>({
    type: "ev_charging/sessions/create",
    ...fields,
  });
  return result.session;
}

// Replaces the selected sessions by one merged session. With dryRun,
// nothing is written and the result is a preview or the unmet conditions.
export function mergeSessions(
  hass: HomeAssistant,
  sessionIds: string[],
  odometerKm: Record<string, number>,
  dryRun: boolean,
): Promise<MergeResult> {
  return hass.callWS<MergeResult>({
    type: "ev_charging/sessions/merge",
    session_ids: sessionIds,
    odometer_km: odometerKm,
    dry_run: dryRun,
  });
}
