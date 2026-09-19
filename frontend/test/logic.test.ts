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
  parseState,
  serializeState,
  shiftMonth,
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
