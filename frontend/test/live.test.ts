import { describe, expect, it } from "vitest";
import {
  monthSolarSharePercent,
  netDurationMinutes,
  plugDurationMinutes,
  solarSharePercent,
  type LivePayload,
} from "../src/live";
import { session } from "./fixtures";

function live(overrides: Partial<LivePayload> = {}): LivePayload {
  return {
    state: "charging",
    active: true,
    wallbox: { name: "Carport", max_power_kw: 11 },
    currency: "EUR",
    session_start: "2026-09-05T18:00:00+02:00",
    vehicle: null,
    vehicle_guest: false,
    identification_source: "unresolved",
    identification_decided: true,
    location: "home",
    soc_start: null,
    soc: null,
    soc_target: null,
    charge_end: null,
    charge_power_kw: 7,
    energy_kwh: 1,
    energy_grid_kwh: null,
    energy_solar_kwh: null,
    grid_share_pct: null,
    cost: null,
    effective_price: null,
    net_duration_min: 30,
    plug_duration_min: 30,
    flagged: false,
    charge_error: false,
    location_conflict: false,
    ...overrides,
  };
}

describe("netDurationMinutes", () => {
  it("keeps counting while charging", () => {
    expect(netDurationMinutes(live(), 0, 120_000)).toBeCloseTo(32);
  });

  it("stops counting while paused", () => {
    expect(netDurationMinutes(live({ state: "paused" }), 0, 120_000)).toBeCloseTo(30);
  });

  it("has no value without a duration", () => {
    expect(netDurationMinutes(live({ net_duration_min: null }), 0, 1000)).toBeNull();
  });
});

describe("plugDurationMinutes", () => {
  it("measures from the session start", () => {
    const now = new Date("2026-09-05T18:45:00+02:00").getTime();
    expect(plugDurationMinutes(live(), now)).toBeCloseTo(45);
  });

  it("has no value without a session", () => {
    expect(plugDurationMinutes(live({ session_start: null }), 0)).toBeNull();
  });
});

describe("solarSharePercent", () => {
  it("is the solar part of the recorded energy", () => {
    expect(solarSharePercent(live({ energy_grid_kwh: 1, energy_solar_kwh: 3 }))).toBeCloseTo(75);
  });

  it("is undefined without a split", () => {
    expect(solarSharePercent(live())).toBeNull();
    expect(solarSharePercent(live({ energy_grid_kwh: 0, energy_solar_kwh: 0 }))).toBeNull();
  });
});

describe("monthSolarSharePercent", () => {
  it("counts only sessions that recorded a split", () => {
    const sessions = [
      session({ energy_kwh: 10, energy_grid_kwh: 2, energy_solar_kwh: 8 }),
      session({ energy_kwh: 100, energy_grid_kwh: null, energy_solar_kwh: null }),
    ];
    expect(monthSolarSharePercent(sessions)).toBeCloseTo(80);
  });

  it("is undefined when no session has a split", () => {
    expect(monthSolarSharePercent([session()])).toBeNull();
    expect(monthSolarSharePercent([])).toBeNull();
  });
});
