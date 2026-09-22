export interface HomeAssistant {
  language: string;
  locale: { language: string };
  config: { currency: string; time_zone: string };
  callWS<T>(message: Record<string, unknown>): Promise<T>;
  connection: {
    subscribeMessage<T>(
      callback: (message: T) => void,
      subscribeMessage: Record<string, unknown>,
    ): Promise<() => Promise<void>>;
    addEventListener(type: "ready" | "disconnected", listener: () => void): void;
    removeEventListener(type: "ready" | "disconnected", listener: () => void): void;
  };
}

export type SessionLocation = "home" | "home_no_wallbox" | "external";
export type ChargeType = "ac" | "dc" | "unknown";
export type ChargeTypeSource = "entity" | "wallbox_config" | "heuristic";
export type SessionStatus = "complete" | "followup_open" | "flagged";
export type IdentificationSource = "rfid" | "emaid" | "vehicle_api" | "manual" | "unresolved";

export interface Phase {
  start: string;
  end: string | null;
  duration_min: number | null;
  energy_kwh: number | null;
  energy_grid_kwh: number | null;
  energy_solar_kwh: number | null;
  cost: number | null;
  power_avg_kw: number | null;
  power_max_kw: number | null;
}

export interface Session {
  id: string;
  vehicle_id: string | null;
  vehicle_name: string | null;
  card_uid: string | null;
  card_label: string | null;
  location: SessionLocation;
  identification_source: IdentificationSource;
  identification_conflict: boolean;
  identification_corrected: boolean;
  plug_start: string;
  plug_end: string | null;
  plug_duration_min: number | null;
  charge_duration_min: number | null;
  pause_duration_min: number | null;
  phases_recorded: boolean;
  soc_start: number | null;
  soc_end: number | null;
  odometer_km: number | null;
  energy_kwh: number | null;
  energy_is_estimate: boolean;
  energy_grid_kwh: number | null;
  energy_solar_kwh: number | null;
  energy_unallocated_kwh: number;
  cost: number | null;
  charge_type: ChargeType;
  charge_type_source: ChargeTypeSource | null;
  power_avg_kw: number | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  location_conflict: boolean;
  provider: string | null;
  note: string | null;
  charge_error: boolean;
  status: SessionStatus;
  open_fields: string[];
  phases: Phase[];
}

export interface Summary {
  count: number;
  energy_kwh: number;
  energy_is_estimate: boolean;
  cost: number;
  charge_duration_min: number;
  open_followups: number;
}

export interface MonthStats extends Summary {
  month: number;
}

export interface YearSummary {
  all: Summary;
  internal: Summary;
  external: Summary;
}

export interface VehicleCard {
  uid: string;
  label: string;
  type: string;
  active: boolean;
}

export interface Vehicle {
  id: string;
  name: string;
  active: boolean;
  is_guest: boolean;
  manufacturer: string | null;
  model: string | null;
  cards: VehicleCard[];
}
