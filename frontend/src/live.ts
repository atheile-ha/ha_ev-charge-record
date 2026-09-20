import { formatDateTime, formatDistance, formatEnergy, formatPercent, formatTime } from "./format";
import type { TextKey, Translate } from "./i18n";
import type { Session } from "./types";

export type LiveState = "idle" | "candidate" | "charging" | "paused" | "error" | "awaiting_final";

export type PlugReport = "connected" | "not_connected" | "unavailable";

// The plug state of the wallbox. While it is not usable during a session, the
// server says since when and when the session is closed for lack of it.
export interface LivePlug {
  state: PlugReport;
  unavailable_since: string | null;
  timeout_at: string | null;
}

// Where the reading of the identification stands. The card is never told
// whether the identification comes from an entity or from a register: for an
// entity there is nothing to read and this is null.
export interface LiveIdentificationRead {
  state: "reading" | "waiting" | "read" | "unreadable";
  sequence: number;
  attempt: number;
  max_attempts: number;
}

export interface LiveCounter {
  authoritative: "total" | "session" | null;
  switched: boolean;
}

// Whether the sources are set up that the split and the cost need.
export interface LiveSources {
  grid_balance: boolean;
  grid_price: boolean;
}

// The live values of the running session, as the server resolves them.
export interface LivePayload {
  state: LiveState;
  state_since: string | null;
  active: boolean;
  phase_count: number;
  waiting_for_power: boolean;
  plug: LivePlug;
  wallbox: { name: string; max_power_kw: number };
  currency: string;
  session_start: string | null;
  vehicle: { id: string; name: string } | null;
  vehicle_guest: boolean;
  identification_source: string | null;
  identification_decided: boolean;
  identification_conflict: boolean;
  identification_read: LiveIdentificationRead | null;
  location: string | null;
  soc_start: number | null;
  soc: number | null;
  soc_target: number | null;
  odometer_km: number | null;
  charge_end: string | null;
  // Why there is no charge end although the vehicle reports one.
  charge_end_missing: "no_power" | null;
  charge_power_kw: number | null;
  energy_kwh: number | null;
  energy_grid_kwh: number | null;
  energy_solar_kwh: number | null;
  grid_share_pct: number | null;
  cost: number | null;
  effective_price: number | null;
  net_duration_min: number | null;
  plug_duration_min: number | null;
  energy_unallocated_kwh: number | null;
  counter: LiveCounter;
  sources: LiveSources;
  flagged: boolean;
  charge_error: boolean;
  location_conflict: boolean;
}

const MS_PER_MINUTE = 60_000;

// The charging time keeps running between two pushes while a phase is open.
export function netDurationMinutes(
  payload: LivePayload,
  receivedAt: number,
  now: number,
): number | null {
  if (payload.net_duration_min === null) {
    return null;
  }
  const running = payload.state === "charging";
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

// Where and how the moments are shown.
export interface LiveFormat {
  locale: string;
  timeZone: string;
  // The present moment in milliseconds, to leave out the date of a moment that is today.
  now: number;
}

// A moment of today shows the time only; an earlier or later day shows the date as well.
export function formatMoment(iso: string, format: LiveFormat): string {
  const day = (ms: number): string =>
    new Intl.DateTimeFormat("en-CA", {
      timeZone: format.timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(ms);
  return day(new Date(iso).getTime()) === day(format.now)
    ? formatTime(iso, format.locale, format.timeZone)
    : formatDateTime(iso, format.locale, format.timeZone);
}

// The title of the card: the charging session of the wallbox, named by the wallbox.
export function titleText(live: LivePayload | undefined, t: Translate): string {
  const name = live?.wallbox.name.trim();
  return name ? t("live_title_wallbox", { name }) : t("live_title");
}

// The state of charge from the start to now, with the target where the vehicle has one.
export function socText(live: LivePayload, t: Translate, locale: string): string | null {
  if (live.soc_start === null && live.soc === null) {
    return null;
  }
  const range =
    live.soc_start !== null && live.soc !== null
      ? `${formatPercent(live.soc_start, locale)} → ${formatPercent(live.soc, locale)}`
      : formatPercent(live.soc ?? live.soc_start, locale);
  return live.soc_target === null
    ? range
    : `${range} (${t("live_soc_target", { target: live.soc_target })})`;
}

// The odometer and the state of charge in one line below the vehicle; null when neither is known.
export function vehicleDetailsText(live: LivePayload, t: Translate, locale: string): string | null {
  const parts = [
    live.odometer_km === null ? null : formatDistance(live.odometer_km, locale),
    socText(live, t, locale),
  ].filter((part): part is string => part !== null);
  return parts.length === 0 ? null : parts.join(" · ");
}

// The expected end of the charging, or why there is none; null where the vehicle has no such value.
export function chargeEndText(live: LivePayload, t: Translate, format: LiveFormat): string | null {
  if (live.charge_end !== null) {
    return formatTime(live.charge_end, format.locale, format.timeZone);
  }
  return live.charge_end_missing === "no_power" ? t("live_charge_end_no_power") : null;
}

// What the card shows without a session: why there is none.
export function idleText(live: LivePayload, t: Translate): string {
  switch (live.plug.state) {
    case "not_connected":
      return t("live_idle_not_connected");
    case "unavailable":
      return t("live_idle_plug_unavailable");
    default:
      return t("live_idle");
  }
}

// The state of the session, with the reason and since when it holds.
export function stateText(live: LivePayload, t: Translate, format: LiveFormat): string {
  const time = live.state_since === null ? null : formatMoment(live.state_since, format);
  switch (live.state) {
    case "candidate":
      return t("live_status_candidate");
    case "charging":
      return time === null ? t("live_state_charging") : t("live_status_charging", { time });
    case "paused":
      if (live.waiting_for_power) {
        return t("live_status_waiting_for_power");
      }
      return time === null ? t("live_status_paused") : t("live_status_paused_since", { time });
    case "error":
      return time === null ? t("live_state_error") : t("live_status_error", { time });
    case "awaiting_final":
      return t("live_status_awaiting_final");
    default:
      return t("live_idle");
  }
}

// How many phases the session has had; nothing before the first.
export function phasesText(live: LivePayload, t: Translate): string | null {
  if (live.phase_count === 0) {
    return null;
  }
  return live.phase_count === 1
    ? t("live_phase_one")
    : t("live_phase_other", { count: live.phase_count });
}

// The plug state of the wallbox. While it is not usable during a session, since
// when, and when the session is closed for lack of it.
export function plugText(live: LivePayload, t: Translate, format: LiveFormat): string {
  const { plug } = live;
  switch (plug.state) {
    case "connected":
      return t("live_plug_connected");
    case "not_connected":
      return t("live_plug_not_connected");
    default:
      if (plug.unavailable_since !== null && plug.timeout_at !== null) {
        return t("live_plug_unavailable_timeout", {
          since: formatMoment(plug.unavailable_since, format),
          timeout: formatMoment(plug.timeout_at, format),
        });
      }
      return t("live_plug_unavailable");
  }
}

// The name shown for the vehicle: while the cascade has not decided, that it is
// being identified, and only afterwards that it is not assigned.
export function vehicleText(live: LivePayload, t: Translate): string {
  if (live.vehicle_guest) {
    return t("live_vehicle_guest");
  }
  if (live.vehicle !== null) {
    return live.vehicle.name;
  }
  return live.identification_decided ? t("unassigned") : t("live_assign_detecting");
}

const IDENTIFICATION_SOURCE_KEYS = {
  rfid: "identification_rfid",
  emaid: "identification_emaid",
  vehicle_api: "identification_vehicle_api",
  manual: "identification_manual",
} as const satisfies Record<string, TextKey>;

// What the assignment rests on, once the cascade has decided and a vehicle is assigned.
export function assignmentText(live: LivePayload, t: Translate): string | null {
  const source = live.identification_source;
  if (!live.identification_decided || live.vehicle === null || source === null) {
    return null;
  }
  const key = (IDENTIFICATION_SOURCE_KEYS as Record<string, TextKey | undefined>)[source];
  return key === undefined ? null : t("live_assign_via", { source: t(key) });
}

// Where the reading of the identification stands; null when nothing is read, and
// when the card was read and the assignment already says what it led to.
export function readingText(live: LivePayload, t: Translate): string | null {
  const read = live.identification_read;
  if (read === null || (read.state === "read" && assignmentText(live, t) !== null)) {
    return null;
  }
  switch (read.state) {
    case "reading":
      return t("live_read_reading", {
        sequence: read.sequence,
        attempt: read.attempt,
        max: read.max_attempts,
      });
    case "waiting":
      return t("live_read_waiting");
    case "read":
      return t("live_read_done");
    default:
      return t("live_read_unreadable");
  }
}

// The energy counter that carries the energy, and that it was switched.
export function counterText(live: LivePayload, t: Translate): string | null {
  const { authoritative, switched } = live.counter;
  if (authoritative === null) {
    return null;
  }
  const counter = t(authoritative === "total" ? "live_counter_total" : "live_counter_session");
  return switched ? t("live_counter_switched", { counter }) : t("live_counter", { counter });
}

// The energy the server measured but could not assign to grid or solar.
export function unallocatedText(live: LivePayload, t: Translate, locale: string): string | null {
  const energy = live.energy_unallocated_kwh;
  if (energy === null || energy <= 0) {
    return null;
  }
  return t("live_unallocated", { energy: formatEnergy(energy, locale) });
}

// Why a value is missing, where the reason is a source that is not set up.
export interface LiveGaps {
  split: string | null;
  cost: string | null;
}

export function dataGaps(live: LivePayload, t: Translate): LiveGaps {
  return {
    split:
      live.energy_grid_kwh === null && !live.sources.grid_balance ? t("live_missing_split") : null,
    cost: live.cost === null && !live.sources.grid_price ? t("live_missing_cost") : null,
  };
}
