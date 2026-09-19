import { describe, expect, it } from "vitest";
import {
  EMPTY,
  formatCost,
  formatDateTime,
  formatDuration,
  formatEnergy,
  monthName,
} from "../src/format";

describe("formatEnergy", () => {
  it("marks an estimate with a tilde", () => {
    expect(formatEnergy(12.5, "en", true)).toBe("~12.50 kWh");
    expect(formatEnergy(12.5, "en", false)).toBe("12.50 kWh");
  });

  it("uses the locale's separators", () => {
    expect(formatEnergy(1234.5, "de")).toBe("1.234,50 kWh");
  });

  it("shows a dash for a missing value", () => {
    expect(formatEnergy(null, "en")).toBe(EMPTY);
  });
});

describe("formatCost", () => {
  it("formats as currency", () => {
    expect(formatCost(13.17, "en", "EUR")).toBe("€13.17");
  });

  it("falls back to a plain number for an unknown currency code", () => {
    expect(formatCost(13.17, "en", "not a currency")).toBe("13.17 not a currency");
  });

  it("shows a dash for a missing value", () => {
    expect(formatCost(null, "en", "EUR")).toBe(EMPTY);
  });
});

describe("formatDuration", () => {
  it("shows minutes below an hour", () => {
    expect(formatDuration(45)).toBe("45 min");
  });

  it("shows hours and padded minutes from an hour on", () => {
    expect(formatDuration(65)).toBe("1:05 h");
    expect(formatDuration(412)).toBe("6:52 h");
  });

  it("shows a dash for a missing value", () => {
    expect(formatDuration(null)).toBe(EMPTY);
  });
});

describe("dates", () => {
  it("renders a moment in the given time zone", () => {
    const text = formatDateTime("2026-09-30T23:30:00+00:00", "en", "Europe/Berlin");
    expect(text).toContain("10/01/2026");
    expect(text).toContain("01:30");
  });

  it("names months in the locale", () => {
    expect(monthName(9, "en", "long")).toBe("September");
    expect(monthName(3, "de", "long")).toBe("März");
  });
});
