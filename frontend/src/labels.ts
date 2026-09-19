import type { Translate } from "./i18n";
import type { Session } from "./types";

// A session without a vehicle is shown as not assigned, not as an error.
export function vehicleLabel(session: Session, t: Translate): string {
  if (session.vehicle_id === null) {
    return t("unassigned");
  }
  return session.vehicle_name ?? session.vehicle_id;
}

const KNOWN_FIELDS = [
  "vehicle_id",
  "soc_start",
  "soc_end",
  "odometer_km",
  "energy_kwh",
  "energy_grid_kwh",
  "energy_solar_kwh",
  "cost",
  "address",
] as const;

type KnownField = (typeof KNOWN_FIELDS)[number];

function isKnownField(name: string): name is KnownField {
  return (KNOWN_FIELDS as readonly string[]).includes(name);
}

export function fieldLabel(name: string, t: Translate): string {
  return isKnownField(name) ? t(`field_${name}`) : name;
}
