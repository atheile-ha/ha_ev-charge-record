import { describe, expect, it } from "vitest";
import {
  odometerPayload,
  pruneSelection,
  sessionsWithoutOdometer,
  toggleSelection,
} from "../src/merge";
import { session } from "./fixtures";

const early = session({ id: "a", plug_start: "2026-09-05T18:00:00+02:00", odometer_km: null });
const late = session({ id: "b", plug_start: "2026-09-05T19:00:00+02:00", odometer_km: null });
const known = session({ id: "c", plug_start: "2026-09-05T20:00:00+02:00", odometer_km: 7699 });

describe("toggleSelection", () => {
  it("adds an id that is not selected and removes one that is", () => {
    expect(toggleSelection(["a"], "b")).toEqual(["a", "b"]);
    expect(toggleSelection(["a", "b"], "a")).toEqual(["b"]);
  });
});

describe("pruneSelection", () => {
  it("drops ids of sessions that no longer exist", () => {
    expect(pruneSelection(["a", "gone", "c"], [early, known])).toEqual(["a", "c"]);
  });
});

describe("sessionsWithoutOdometer", () => {
  it("returns the selected sessions without a reading, earliest first", () => {
    expect(sessionsWithoutOdometer(["c", "b", "a"], [late, known, early])).toEqual([early, late]);
  });

  it("ignores sessions that are not selected", () => {
    expect(sessionsWithoutOdometer(["c"], [early, known])).toEqual([]);
  });
});

describe("odometerPayload", () => {
  it("sends only valid readings entered for sessions without one", () => {
    const payload = odometerPayload([early, late], {
      a: " 7699.5 ",
      b: "abc",
      c: "7000",
    });
    expect(payload).toEqual({ a: 7699.5 });
  });

  it("leaves out empty and negative input", () => {
    expect(odometerPayload([early, late], { a: "", b: "-1" })).toEqual({});
  });
});
