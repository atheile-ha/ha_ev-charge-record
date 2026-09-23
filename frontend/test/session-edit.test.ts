import { describe, expect, it } from "vitest";
import {
  buildUpdatePayload,
  fieldsForCorrection,
  fieldsForOpenSession,
  hasUpdatePayload,
} from "../src/session-edit";
import { session } from "./fixtures";

describe("fieldsForOpenSession", () => {
  it("offers exactly the fields that can fill the session's open_fields", () => {
    const open = session({ open_fields: ["soc_end", "odometer_km", "cost"] });
    expect(fieldsForOpenSession(open)).toEqual(["soc_end", "odometer_km", "cost"]);
  });

  it("offers soc_start, soc_end and energy_billed_kwh for an open energy_kwh", () => {
    const open = session({ open_fields: ["energy_kwh"] });
    expect(fieldsForOpenSession(open)).toEqual(["soc_start", "soc_end", "energy_billed_kwh"]);
  });

  it("offers nothing for a session with no open fields", () => {
    expect(fieldsForOpenSession(session({ open_fields: [] }))).toEqual([]);
  });

  it("does not offer a field for the vehicle_id gap, which is handled separately", () => {
    expect(fieldsForOpenSession(session({ open_fields: ["vehicle_id"] }))).toEqual([]);
  });
});

describe("fieldsForCorrection", () => {
  it("excludes charge_type unless it was determined heuristically", () => {
    const wallboxSourced = session({ charge_type_source: "wallbox_config" });
    expect(fieldsForCorrection(wallboxSourced)).not.toContain("charge_type");

    const heuristic = session({ charge_type_source: "heuristic" });
    expect(fieldsForCorrection(heuristic)).toContain("charge_type");
  });

  it("excludes plug_end once the session already has one", () => {
    const finished = session({ plug_end: "2026-09-05T20:12:04+02:00" });
    expect(fieldsForCorrection(finished)).not.toContain("plug_end");

    const open = session({ plug_end: null });
    expect(fieldsForCorrection(open)).toContain("plug_end");
  });

  it("always offers the plain correctable fields", () => {
    const fields = fieldsForCorrection(session());
    expect(fields).toEqual(
      expect.arrayContaining([
        "soc_start",
        "soc_end",
        "odometer_km",
        "energy_billed_kwh",
        "cost",
        "address",
        "note",
        "provider",
      ]),
    );
  });
});

describe("buildUpdatePayload", () => {
  it("converts numeric fields and passes text fields through", () => {
    expect(
      buildUpdatePayload({
        soc_start: "20",
        soc_end: "80.5",
        odometer_km: "12345",
        energy_billed_kwh: "10.2",
        cost: "3.5",
        charge_type: "dc",
        address: "Somewhere 1",
        note: "a note",
        provider: "ACME",
        plug_end: "2026-09-05T20:00",
      }),
    ).toEqual({
      soc_start: 20,
      soc_end: 80.5,
      odometer_km: 12345,
      energy_billed_kwh: 10.2,
      cost: 3.5,
      charge_type: "dc",
      address: "Somewhere 1",
      note: "a note",
      provider: "ACME",
      plug_end: new Date("2026-09-05T20:00").toISOString(),
    });
  });

  it("leaves out a field that was never touched", () => {
    expect(buildUpdatePayload({ soc_start: "20" })).toEqual({ soc_start: 20 });
  });

  it("leaves out a field the user cleared back to blank", () => {
    expect(buildUpdatePayload({ soc_start: "" })).toEqual({});
  });

  it("returns an empty payload for empty values", () => {
    expect(buildUpdatePayload({})).toEqual({});
  });
});

describe("hasUpdatePayload", () => {
  it("is false while nothing was typed", () => {
    expect(hasUpdatePayload({})).toBe(false);
    expect(hasUpdatePayload({ soc_start: "" })).toBe(false);
  });

  it("is true once a field has a value", () => {
    expect(hasUpdatePayload({ note: "seen" })).toBe(true);
  });
});
