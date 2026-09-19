import { beforeEach, describe, expect, it, vi } from "vitest";
import de from "../../custom_components/ev_charging/translations/de.json";
import { clearTranslateCache, loadTranslate, makeTranslate } from "../src/i18n";
import type { HomeAssistant } from "../src/types";

const PREFIX = "component.ev_charging.selector.panel.options.";

function prefixed(options: Record<string, string>): Record<string, string> {
  return Object.fromEntries(Object.entries(options).map(([key, text]) => [PREFIX + key, text]));
}

function fakeHass(callWS: HomeAssistant["callWS"], language = "de"): HomeAssistant {
  return { language, locale: { language }, config: { currency: "EUR", time_zone: "UTC" }, callWS };
}

describe("makeTranslate", () => {
  const t = makeTranslate(prefixed(de.selector.panel.options));

  it("returns the translated text", () => {
    expect(t("view_overview")).toBe("Übersicht");
  });

  it("fills placeholders", () => {
    expect(t("filter_count", { shown: 3, total: 10 })).toBe("3 von 10 Ladevorgängen");
  });

  it("leaves an unknown placeholder untouched", () => {
    expect(t("filter_count", { shown: 3 })).toBe("3 von {total} Ladevorgängen");
  });

  it("returns the key itself when the text is missing", () => {
    expect(makeTranslate({})("view_overview")).toBe("view_overview");
  });
});

describe("loadTranslate", () => {
  beforeEach(() => clearTranslateCache());

  it("asks the frontend for the integration's texts once per language", async () => {
    const callWS = vi.fn().mockResolvedValue({ resources: prefixed({ loading: "Wird geladen …" }) });
    const hass = fakeHass(callWS as HomeAssistant["callWS"]);

    const first = await loadTranslate(hass);
    await loadTranslate(hass);

    expect(first("loading")).toBe("Wird geladen …");
    expect(callWS).toHaveBeenCalledTimes(1);
    expect(callWS).toHaveBeenCalledWith({
      type: "frontend/get_translations",
      language: "de",
      category: "selector",
      integration: ["ev_charging"],
    });
  });

  it("does not keep a failed request", async () => {
    const callWS = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ resources: prefixed({ loading: "ok" }) });
    const hass = fakeHass(callWS as HomeAssistant["callWS"]);

    await expect(loadTranslate(hass)).rejects.toThrow("offline");
    const t = await loadTranslate(hass);

    expect(t("loading")).toBe("ok");
    expect(callWS).toHaveBeenCalledTimes(2);
  });
});
