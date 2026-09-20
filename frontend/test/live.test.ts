import { describe, expect, it } from "vitest";
import de from "../../custom_components/ev_charging/translations/de.json";
import en from "../../custom_components/ev_charging/translations/en.json";
import { makeTranslate } from "../src/i18n";
import {
  assignmentText,
  chargeEndText,
  counterText,
  dataGaps,
  formatMoment,
  idleText,
  monthSolarSharePercent,
  netDurationMinutes,
  phasesText,
  plugDurationMinutes,
  plugText,
  readingText,
  socText,
  solarSharePercent,
  stateText,
  titleText,
  unallocatedText,
  vehicleDetailsText,
  vehicleText,
  type LiveFormat,
  type LivePayload,
} from "../src/live";
import { session } from "./fixtures";

const PREFIX = "component.ev_charging.selector.panel.options.";

function prefixed(options: Record<string, string>): Record<string, string> {
  return Object.fromEntries(Object.entries(options).map(([key, text]) => [PREFIX + key, text]));
}

const tDe = makeTranslate(prefixed(de.selector.panel.options));
const tEn = makeTranslate(prefixed(en.selector.panel.options));

// Half past eight in the evening of the day the session runs, in Berlin.
const NOW = new Date("2026-09-05T20:30:00+02:00").getTime();
const FORMAT_DE: LiveFormat = { locale: "de", timeZone: "Europe/Berlin", now: NOW };
const FORMAT_EN: LiveFormat = { locale: "en-GB", timeZone: "Europe/Berlin", now: NOW };

function live(overrides: Partial<LivePayload> = {}): LivePayload {
  return {
    state: "charging",
    state_since: "2026-09-05T18:12:00+02:00",
    active: true,
    phase_count: 1,
    waiting_for_power: false,
    plug: { state: "connected", unavailable_since: null, timeout_at: null },
    wallbox: { name: "Carport", max_power_kw: 11 },
    currency: "EUR",
    session_start: "2026-09-05T18:00:00+02:00",
    vehicle: null,
    vehicle_guest: false,
    identification_source: "unresolved",
    identification_decided: true,
    identification_conflict: false,
    identification_read: null,
    location: "home",
    soc_start: null,
    soc: null,
    soc_target: null,
    odometer_km: null,
    charge_end: null,
    charge_end_missing: null,
    charge_power_kw: 7,
    energy_kwh: 1,
    energy_grid_kwh: null,
    energy_solar_kwh: null,
    grid_share_pct: null,
    cost: null,
    effective_price: null,
    net_duration_min: 30,
    plug_duration_min: 30,
    energy_unallocated_kwh: 0,
    counter: { authoritative: "total", switched: false },
    sources: { grid_balance: true, grid_price: true },
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

  it("does not count while the session is only a candidate", () => {
    expect(
      netDurationMinutes(live({ state: "candidate", net_duration_min: 0 }), 0, 120_000),
    ).toBe(0);
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

describe("formatMoment", () => {
  it("shows only the time for a moment of today", () => {
    expect(formatMoment("2026-09-05T18:12:00+02:00", FORMAT_DE)).toBe("18:12");
  });

  it("adds the date for another day", () => {
    const text = formatMoment("2026-09-04T22:10:00+02:00", FORMAT_DE);
    expect(text).toContain("04.09.2026");
    expect(text).toContain("22:10");
  });

  it("takes the day in the time zone of the installation, not the machine's", () => {
    // Same day in UTC, but after midnight in Berlin.
    const afterMidnight = new Date("2026-09-05T22:10:00Z").getTime();
    const format = { ...FORMAT_DE, now: afterMidnight };
    expect(formatMoment("2026-09-05T21:30:00Z", format)).toContain("05.09.2026");
  });
});

describe("titleText", () => {
  it("names the charging session by the wallbox", () => {
    expect(titleText(live(), tDe)).toBe("Ladevorgang Carport");
    expect(titleText(live(), tEn)).toBe("Charging session Carport");
  });

  it("has no name before the first values arrive", () => {
    expect(titleText(undefined, tDe)).toBe("Ladevorgang");
    expect(titleText(live({ wallbox: { name: " ", max_power_kw: 11 } }), tDe)).toBe("Ladevorgang");
  });
});

describe("socText", () => {
  it("gives the start and the present value with the target", () => {
    expect(socText(live({ soc_start: 24, soc: 45, soc_target: 80 }), tDe, "de")).toBe(
      "24 % → 45 % (Ziel 80 %)",
    );
    expect(socText(live({ soc_start: 24, soc: 45, soc_target: 80 }), tEn, "en-GB")).toBe(
      "24 % → 45 % (target 80 %)",
    );
  });

  it("gives the one value that is known", () => {
    expect(socText(live({ soc_start: 24 }), tDe, "de")).toBe("24 %");
    expect(socText(live({ soc: 45 }), tDe, "de")).toBe("45 %");
  });

  it("says nothing without a value", () => {
    expect(socText(live({ soc_target: 80 }), tDe, "de")).toBeNull();
  });
});

describe("vehicleDetailsText", () => {
  it("puts the odometer and the state of charge in one line", () => {
    const details = live({ odometer_km: 9969, soc_start: 24, soc: 45, soc_target: 80 });
    expect(vehicleDetailsText(details, tDe, "de")).toBe("9.969 km · 24 % → 45 % (Ziel 80 %)");
  });

  it("leaves out what is not known", () => {
    expect(vehicleDetailsText(live({ odometer_km: 9969 }), tDe, "de")).toBe("9.969 km");
    expect(vehicleDetailsText(live({ soc: 45 }), tDe, "de")).toBe("45 %");
    expect(vehicleDetailsText(live(), tDe, "de")).toBeNull();
  });
});

describe("chargeEndText", () => {
  it("gives the time of the expected end", () => {
    const charging = live({ charge_end: "2026-09-05T20:45:00+02:00" });
    expect(chargeEndText(charging, tDe, FORMAT_DE)).toBe("20:45");
  });

  it("says that the end is not available without charging power", () => {
    const paused = live({ state: "paused", charge_end_missing: "no_power" });
    expect(chargeEndText(paused, tDe, FORMAT_DE)).toBe("Ohne Ladeleistung nicht verfügbar");
    expect(chargeEndText(paused, tEn, FORMAT_EN)).toBe("Not available without charging power");
  });

  it("says nothing where the vehicle has no such value", () => {
    expect(chargeEndText(live(), tDe, FORMAT_DE)).toBeNull();
  });
});

describe("idleText", () => {
  it("says that no vehicle is connected", () => {
    const text = idleText(
      live({ active: false, plug: { state: "not_connected", unavailable_since: null, timeout_at: null } }),
      tDe,
    );
    expect(text).toBe("Kein Fahrzeug verbunden");
  });

  it("says that the plug state is not available", () => {
    const text = idleText(
      live({ active: false, plug: { state: "unavailable", unavailable_since: null, timeout_at: null } }),
      tDe,
    );
    expect(text).toBe("Steckerzustand nicht verfügbar");
  });

  it("falls back to no session running", () => {
    expect(idleText(live({ active: false }), tDe)).toBe("Kein Ladevorgang aktiv");
    expect(idleText(live({ active: false }), tEn)).toBe("No charging session running");
  });
});

describe("stateText", () => {
  it("says that the session is being detected", () => {
    expect(stateText(live({ state: "candidate" }), tDe, FORMAT_DE)).toBe(
      "Ladevorgang wird erkannt",
    );
    expect(stateText(live({ state: "candidate" }), tEn, FORMAT_EN)).toBe(
      "Charging session is being detected",
    );
  });

  it("says that the session waits for charging power before the first phase", () => {
    const waiting = live({ state: "paused", waiting_for_power: true, phase_count: 0 });
    expect(stateText(waiting, tDe, FORMAT_DE)).toBe("Wartet auf Ladeleistung");
    expect(stateText(waiting, tEn, FORMAT_EN)).toBe("Waiting for charging power");
  });

  it("says since when a session that has charged is paused", () => {
    const paused = live({ state: "paused", state_since: "2026-09-05T19:05:00+02:00" });
    expect(stateText(paused, tDe, FORMAT_DE)).toBe("Pause seit 19:05");
    expect(stateText(paused, tEn, FORMAT_EN)).toBe("Paused since 19:05");
  });

  it("says since when the session charges or has an error", () => {
    expect(stateText(live(), tDe, FORMAT_DE)).toBe("Lädt seit 18:12");
    expect(stateText(live({ state: "error" }), tDe, FORMAT_DE)).toBe("Ladefehler seit 18:12");
  });

  it("says that the vehicle was unplugged and the final values are read", () => {
    expect(stateText(live({ state: "awaiting_final" }), tDe, FORMAT_DE)).toBe(
      "Abgesteckt, Endwerte werden gelesen",
    );
  });

  it("names the state without a moment when the server sent none", () => {
    expect(stateText(live({ state_since: null }), tDe, FORMAT_DE)).toBe("Lädt");
    expect(stateText(live({ state: "paused", state_since: null }), tDe, FORMAT_DE)).toBe("Pause");
  });

  it("gives the date for a state that began on another day", () => {
    const paused = live({ state: "paused", state_since: "2026-09-04T22:10:00+02:00" });
    expect(stateText(paused, tDe, FORMAT_DE)).toContain("04.09.2026");
  });
});

describe("phasesText", () => {
  it("says nothing before the first phase", () => {
    expect(phasesText(live({ phase_count: 0 }), tDe)).toBeNull();
  });

  it("counts the phases so far", () => {
    expect(phasesText(live({ phase_count: 1 }), tDe)).toBe("Bisher 1 Ladephase");
    expect(phasesText(live({ phase_count: 3 }), tDe)).toBe("Bisher 3 Ladephasen");
    expect(phasesText(live({ phase_count: 3 }), tEn)).toBe("3 phases so far");
  });
});

describe("plugText", () => {
  it("names the connector state", () => {
    expect(plugText(live(), tDe, FORMAT_DE)).toBe("Fahrzeug verbunden");
    const off = live({ plug: { state: "not_connected", unavailable_since: null, timeout_at: null } });
    expect(plugText(off, tDe, FORMAT_DE)).toBe("Kein Fahrzeug verbunden");
  });

  it("says since when the state is not available and when the session closes", () => {
    const lost = live({
      plug: {
        state: "unavailable",
        unavailable_since: "2026-09-05T19:00:00+02:00",
        timeout_at: "2026-09-06T07:00:00+02:00",
      },
    });
    const text = plugText(lost, tDe, FORMAT_DE);
    expect(text).toContain("seit 19:00");
    expect(text).toContain("06.09.2026");
    expect(text).toContain("07:00");
  });

  it("names an unavailable state without a session", () => {
    const lost = live({
      active: false,
      plug: { state: "unavailable", unavailable_since: null, timeout_at: null },
    });
    expect(plugText(lost, tDe, FORMAT_DE)).toBe("Steckerzustand nicht verfügbar");
  });
});

describe("vehicleText", () => {
  it("says the vehicle is being identified until the cascade has decided", () => {
    expect(vehicleText(live({ identification_decided: false }), tDe)).toBe(
      "Fahrzeug wird erkannt",
    );
  });

  it("says not assigned only after the decision", () => {
    expect(vehicleText(live({ identification_decided: true }), tDe)).toBe("Nicht zugeordnet");
  });

  it("names the vehicle, or a guest", () => {
    expect(vehicleText(live({ vehicle: { id: "v001", name: "Car One" } }), tDe)).toBe("Car One");
    expect(vehicleText(live({ vehicle_guest: true }), tDe)).toBe("Gastfahrzeug");
  });
});

describe("assignmentText", () => {
  it("says what the assignment rests on", () => {
    const rfid = live({ vehicle: { id: "v001", name: "Car One" }, identification_source: "rfid" });
    expect(assignmentText(rfid, tDe)).toBe("Zuordnung über RFID-Karte");
    const api = live({
      vehicle: { id: "v001", name: "Car One" },
      identification_source: "vehicle_api",
    });
    expect(assignmentText(api, tEn)).toBe("Assigned by Vehicle integration");
  });

  it("says nothing before the decision or without a vehicle", () => {
    const undecided = live({
      vehicle: { id: "v001", name: "Car One" },
      identification_source: "rfid",
      identification_decided: false,
    });
    expect(assignmentText(undecided, tDe)).toBeNull();
    expect(assignmentText(live(), tDe)).toBeNull();
  });
});

describe("readingText", () => {
  const read = (state: "reading" | "waiting" | "read" | "unreadable", sequence = 1, attempt = 3) =>
    live({ identification_read: { state, sequence, attempt, max_attempts: 10 } });

  it("says nothing when no identification is read", () => {
    expect(readingText(live(), tDe)).toBeNull();
  });

  it("gives sequence, attempt and maximum while reading", () => {
    expect(readingText(read("reading", 2, 4), tDe)).toBe(
      "Kennung wird gelesen: Folge 2, Versuch 4 von 10",
    );
    expect(readingText(read("reading", 2, 4), tEn)).toBe(
      "Reading the card: sequence 2, attempt 4 of 10",
    );
  });

  it("says that the next attempt follows with the first charging", () => {
    expect(readingText(read("waiting", 1, 10), tDe)).toBe(
      "Kennung noch nicht gelesen, der nächste Versuch folgt mit dem Ladebeginn",
    );
  });

  it("says that the card was read, or cannot be read", () => {
    expect(readingText(read("read"), tDe)).toBe("Kennung gelesen");
    expect(readingText(read("unreadable", 2, 10), tDe)).toBe("Kennung nicht lesbar");
  });

  it("does not repeat that the card was read where the assignment says so", () => {
    const assigned = live({
      vehicle: { id: "v001", name: "Car One" },
      identification_source: "rfid",
      identification_read: { state: "read", sequence: 1, attempt: 2, max_attempts: 10 },
    });
    expect(assignmentText(assigned, tDe)).toBe("Zuordnung über RFID-Karte");
    expect(readingText(assigned, tDe)).toBeNull();
  });

  it("still says that the card was read while nothing is assigned", () => {
    const unassigned = live({
      identification_read: { state: "read", sequence: 1, attempt: 2, max_attempts: 10 },
    });
    expect(readingText(unassigned, tDe)).toBe("Kennung gelesen");
  });
});

describe("counterText", () => {
  it("names the counter that carries the energy", () => {
    expect(counterText(live(), tDe)).toBe("Energiezähler: Gesamtzähler");
    expect(counterText(live({ counter: { authoritative: "session", switched: false } }), tEn)).toBe(
      "Energy counter: session counter",
    );
  });

  it("says that it was switched", () => {
    const switched = live({ counter: { authoritative: "session", switched: true } });
    expect(counterText(switched, tDe)).toBe("Energiezähler: Sitzungszähler, automatisch gewechselt");
  });

  it("says nothing without a session", () => {
    expect(counterText(live({ counter: { authoritative: null, switched: false } }), tDe)).toBeNull();
  });
});

describe("unallocatedText", () => {
  it("names energy that could not be allocated", () => {
    expect(unallocatedText(live({ energy_unallocated_kwh: 0.25 }), tDe, "de")).toBe(
      "Energie nicht aufgeteilt: 0,250 kWh",
    );
  });

  it("says nothing when all energy was allocated or there is no session", () => {
    expect(unallocatedText(live({ energy_unallocated_kwh: 0 }), tDe, "de")).toBeNull();
    expect(unallocatedText(live({ energy_unallocated_kwh: null }), tDe, "de")).toBeNull();
  });
});

describe("dataGaps", () => {
  it("gives the reason instead of a missing split and a missing cost", () => {
    const bare = live({ sources: { grid_balance: false, grid_price: false } });
    expect(dataGaps(bare, tDe)).toEqual({
      split: "Keine Aufteilung in Netz- und Sonnenanteil ohne Netzsaldo",
      cost: "Keine Kosten ohne Netzpreis",
    });
    expect(dataGaps(bare, tEn).cost).toBe("No cost without a grid price");
  });

  it("gives no reason where the value is there or its sources are set up", () => {
    const complete = live({ energy_grid_kwh: 1, energy_solar_kwh: 2, cost: 0.5 });
    expect(dataGaps(complete, tDe)).toEqual({ split: null, cost: null });
    const values = live({
      energy_grid_kwh: 1,
      energy_solar_kwh: 2,
      cost: 0.5,
      sources: { grid_balance: false, grid_price: false },
    });
    expect(dataGaps(values, tDe)).toEqual({ split: null, cost: null });
  });
});

describe("texts of the live card", () => {
  it("exist in both languages", () => {
    const keys = Object.keys(en.selector.panel.options).filter((key) => key.startsWith("live_"));
    expect(keys.length).toBeGreaterThan(30);
    for (const key of keys) {
      expect(Object.keys(de.selector.panel.options)).toContain(key);
    }
  });
});
