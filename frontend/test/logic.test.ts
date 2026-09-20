import { describe, expect, it } from "vitest";
import {
  EMPTY_FILTERS,
  NO_CARD,
  UNASSIGNED,
  applyFilters,
  cardOptions,
  currentYearMonth,
  defaultState,
  hasActiveFilter,
  mapUrl,
  monthOfSession,
  monthlySummaries,
  parseState,
  phasesNotice,
  serializeState,
  sessionsOfMonth,
  shiftMonth,
  summarizeSessions,
  summarizeYear,
  vehicleOptions,
  yearOptions,
} from "../src/logic";
import { session } from "./fixtures";

describe("shiftMonth", () => {
  it("moves within a year", () => {
    expect(shiftMonth(2026, 5, 1)).toEqual({ year: 2026, month: 6 });
  });

  it("wraps forward over the year boundary", () => {
    expect(shiftMonth(2026, 12, 1)).toEqual({ year: 2027, month: 1 });
  });

  it("wraps backward over the year boundary", () => {
    expect(shiftMonth(2026, 1, -1)).toEqual({ year: 2025, month: 12 });
  });
});

describe("currentYearMonth", () => {
  it("uses the given time zone, not the machine's", () => {
    const instant = new Date("2026-12-31T23:30:00Z");
    expect(currentYearMonth(instant, "Europe/Berlin")).toEqual({ year: 2027, month: 1 });
    expect(currentYearMonth(instant, "UTC")).toEqual({ year: 2026, month: 12 });
  });
});

describe("state in the address", () => {
  it("round-trips view, period and filters", () => {
    const state = {
      view: "detail" as const,
      year: 2026,
      month: 9,
      filters: { ...EMPTY_FILTERS, vehicle: "v001", status: "flagged" },
    };
    const [path, search] = serializeState(state).split("?");
    expect(parseState(path, `?${search}`)).toEqual(state);
  });

  it("never writes the card filter into the address", () => {
    const url = serializeState({
      view: "detail",
      year: 2026,
      month: 9,
      filters: { ...EMPTY_FILTERS, card: "BAEB2194" },
    });
    expect(url).not.toContain("BAEB2194");
    expect(url).not.toContain("card");
  });

  it("ignores values that are out of range", () => {
    expect(parseState("/bogus", "?year=abc&month=13")).toEqual({});
    expect(parseState("/overview", "?year=2026&month=0")).toEqual({ view: "overview" });
  });

  it("accepts the view with the last sessions", () => {
    expect(parseState("/recent", "")).toEqual({ view: "recent" });
  });

  it("falls back to the defaults for an empty address", () => {
    expect(parseState("", "")).toEqual({});
  });
});

describe("defaultState", () => {
  it("opens the overview on the current month without filters", () => {
    expect(defaultState(new Date("2026-09-19T10:00:00Z"), "Europe/Berlin")).toEqual({
      view: "overview",
      year: 2026,
      month: 9,
      filters: EMPTY_FILTERS,
    });
  });
});

describe("applyFilters", () => {
  const assigned = session({ id: "a", vehicle_id: "v001", card_uid: "AAAA" });
  const unassigned = session({ id: "b", vehicle_id: null, vehicle_name: null });
  const external = session({ id: "c", location: "external", charge_type: "dc", status: "flagged" });
  const all = [assigned, unassigned, external];

  it("returns everything without filters", () => {
    expect(applyFilters(all, EMPTY_FILTERS)).toEqual(all);
    expect(hasActiveFilter(EMPTY_FILTERS)).toBe(false);
  });

  it("keeps unassigned sessions visible and selectable on their own", () => {
    expect(applyFilters(all, EMPTY_FILTERS)).toContain(unassigned);
    expect(applyFilters(all, { ...EMPTY_FILTERS, vehicle: UNASSIGNED })).toEqual([unassigned]);
  });

  it("filters by vehicle without matching unassigned sessions", () => {
    expect(applyFilters(all, { ...EMPTY_FILTERS, vehicle: "v001" })).toEqual([assigned, external]);
  });

  it("filters by location, charge type and status", () => {
    expect(applyFilters(all, { ...EMPTY_FILTERS, location: "external" })).toEqual([external]);
    expect(applyFilters(all, { ...EMPTY_FILTERS, chargeType: "dc" })).toEqual([external]);
    expect(applyFilters(all, { ...EMPTY_FILTERS, status: "flagged" })).toEqual([external]);
  });

  it("filters by card and by no card", () => {
    expect(applyFilters(all, { ...EMPTY_FILTERS, card: "AAAA" })).toEqual([assigned]);
    expect(applyFilters(all, { ...EMPTY_FILTERS, card: NO_CARD })).toEqual([unassigned, external]);
  });

  it("combines filters", () => {
    expect(applyFilters(all, { ...EMPTY_FILTERS, vehicle: "v001", location: "external" })).toEqual([
      external,
    ]);
  });
});

describe("filter options", () => {
  it("lists configured vehicles, then removed ones under their recorded name", () => {
    const options = vehicleOptions(
      [
        {
          id: "v001",
          name: "Car One",
          active: true,
          is_guest: false,
          manufacturer: null,
          model: null,
          cards: [],
        },
      ],
      [session({ vehicle_id: "v009", vehicle_name: "Old Car" }), session({ vehicle_id: "v001" })],
    );
    expect(options).toEqual([
      { value: "v001", label: "Car One" },
      { value: "v009", label: "Old Car" },
    ]);
  });

  it("lists each card of the sessions once, by label", () => {
    const options = cardOptions(
      [],
      [
        session({ card_uid: "AAAA", card_label: "Blue" }),
        session({ card_uid: "AAAA", card_label: "Blue" }),
        session({ card_uid: null }),
      ],
      "",
    );
    expect(options).toEqual([{ value: "AAAA", label: "Blue" }]);
  });

  it("offers configured cards even when no session of the month used them", () => {
    const options = cardOptions(
      [{ uid: "1122334455667788", label: "Green", type: "rfid", active: true }],
      [session({ card_uid: "AAAA", card_label: "Blue" })],
      "",
    );
    expect(options).toEqual([
      { value: "1122334455667788", label: "Green" },
      { value: "AAAA", label: "Blue" },
    ]);
  });

  it("merges a configured card with the shortened identifier a wallbox reported", () => {
    const options = cardOptions(
      [{ uid: "0011AABBCCDD", label: "Green", type: "rfid", active: true }],
      [session({ card_uid: "AABBCCDD", card_label: null })],
      "",
    );
    expect(options).toEqual([{ value: "AABBCCDD", label: "Green" }]);
  });

  it("keeps a selected card that is not in the current month", () => {
    expect(cardOptions([], [], "ZZZZ")).toEqual([{ value: "ZZZZ", label: "ZZZZ" }]);
  });

  it("offers the available years, the current one and the selected one, newest first", () => {
    expect(yearOptions([2025, 2026], 2027, 2024)).toEqual([2027, 2026, 2025, 2024]);
  });
});

describe("summarizeSessions", () => {
  it("sums exactly the given sessions", () => {
    const all = [
      session({ energy_kwh: 10.5, cost: 3, charge_duration_min: 60 }),
      session({ energy_kwh: 4.25, cost: null, charge_duration_min: 30, energy_is_estimate: true }),
      session({ energy_kwh: null, cost: 1.5, charge_duration_min: null, status: "followup_open" }),
      session({ energy_kwh: 1, cost: 0, charge_duration_min: 10, open_fields: ["soc_end"] }),
    ];
    expect(summarizeSessions(all)).toEqual({
      count: 4,
      energy_kwh: 15.75,
      energy_is_estimate: true,
      cost: 4.5,
      charge_duration_min: 100,
      open_followups: 2,
    });
    expect(summarizeSessions(all.slice(0, 1))).toMatchObject({
      count: 1,
      energy_kwh: 10.5,
      energy_is_estimate: false,
      open_followups: 0,
    });
  });

  it("is empty for no sessions", () => {
    expect(summarizeSessions([])).toEqual({
      count: 0,
      energy_kwh: 0,
      energy_is_estimate: false,
      cost: 0,
      charge_duration_min: 0,
      open_followups: 0,
    });
  });

  it("follows the filters", () => {
    const sessions = [
      session({ vehicle_id: "v001", energy_kwh: 10 }),
      session({ vehicle_id: null, vehicle_name: null, energy_kwh: 5 }),
    ];
    const visible = applyFilters(sessions, { ...EMPTY_FILTERS, vehicle: UNASSIGNED });
    expect(summarizeSessions(visible).energy_kwh).toBe(5);
  });
});

describe("mapUrl", () => {
  it("prefers the coordinates", () => {
    expect(mapUrl(session({ latitude: 53.5, longitude: 10.25, address: "Somewhere 1" }))).toBe(
      "https://www.google.com/maps/search/?api=1&query=53.5%2C10.25",
    );
  });

  it("falls back to the address", () => {
    expect(mapUrl(session({ address: "Test Street 1, Testville" }))).toBe(
      "https://www.google.com/maps/search/?api=1&query=Test%20Street%201%2C%20Testville",
    );
  });

  it("is absent without a place", () => {
    expect(mapUrl(session())).toBeNull();
  });
});

describe("month of a session", () => {
  const berlin = "Europe/Berlin";

  it("follows the local plug_start, not the UTC month", () => {
    const start = session({ plug_start: "2026-09-30T23:30:00+00:00" });
    expect(monthOfSession(start, berlin)).toBe(10);
    expect(monthOfSession(start, "UTC")).toBe(9);
  });

  it("ignores the end of the session", () => {
    const overNewYear = session({
      plug_start: "2026-12-31T23:30:00+01:00",
      plug_end: "2027-01-01T02:00:00+01:00",
    });
    expect(monthOfSession(overNewYear, berlin)).toBe(12);
  });

  it("selects the sessions of one month", () => {
    const may = session({ id: "may", plug_start: "2026-05-03T08:00:00+02:00" });
    const june = session({ id: "june", plug_start: "2026-06-01T08:00:00+02:00" });
    expect(sessionsOfMonth([may, june], 5, berlin)).toEqual([may]);
  });
});

describe("summaries of a year", () => {
  const berlin = "Europe/Berlin";
  const home = session({ id: "h", plug_start: "2026-01-10T08:00:00+01:00", energy_kwh: 10 });
  const noWallbox = session({
    id: "n",
    plug_start: "2026-01-20T08:00:00+01:00",
    location: "home_no_wallbox",
    energy_kwh: 5,
  });
  const external = session({
    id: "e",
    plug_start: "2026-03-05T08:00:00+01:00",
    location: "external",
    energy_kwh: 30,
  });
  const all = [home, noWallbox, external];

  it("gives twelve months with the sums of each", () => {
    const months = monthlySummaries(all, berlin);
    expect(months).toHaveLength(12);
    expect(months[0]).toMatchObject({ month: 1, count: 2, energy_kwh: 15 });
    expect(months[2]).toMatchObject({ month: 3, count: 1, energy_kwh: 30 });
    expect(months[1].count).toBe(0);
  });

  it("counts home sessions with and without wallbox as internal", () => {
    const summary = summarizeYear(all);
    expect(summary.all.count).toBe(3);
    expect(summary.internal).toMatchObject({ count: 2, energy_kwh: 15 });
    expect(summary.external).toMatchObject({ count: 1, energy_kwh: 30 });
  });

  it("follows the filters when they are applied first", () => {
    const filtered = applyFilters(all, { ...EMPTY_FILTERS, location: "external" });
    expect(monthlySummaries(filtered, berlin)[0].count).toBe(0);
    expect(summarizeYear(filtered).all.energy_kwh).toBe(30);
    expect(summarizeYear(filtered).internal.count).toBe(0);
  });
});

describe("phasesNotice", () => {
  it("says the phases were not recorded for an imported session", () => {
    expect(phasesNotice(session({ phases_recorded: false, phases: [] }))).toBe(
      "detail_phases_not_recorded",
    );
  });

  it("says that a session without any phase has none", () => {
    expect(phasesNotice(session({ phases_recorded: true, phases: [] }))).toBe(
      "detail_no_phases",
    );
  });

  it("has no notice when there are phases to list", () => {
    const phase = {
      start: "2026-09-05T18:12:04+02:00",
      end: "2026-09-05T19:12:04+02:00",
      duration_min: 60,
      energy_kwh: 5,
      energy_grid_kwh: null,
      energy_solar_kwh: null,
      cost: null,
      power_avg_kw: 5,
      power_max_kw: 6,
    };
    expect(phasesNotice(session({ phases_recorded: true, phases: [phase] }))).toBeNull();
  });
});
