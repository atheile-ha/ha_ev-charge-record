import type en from "../../custom_components/ev_charging/translations/en.json";
import type { HomeAssistant } from "./types";

// Every key must exist in the translation files; the compiler rejects a typo.
export type TextKey = keyof (typeof en)["selector"]["panel"]["options"];

export type Translate = (key: TextKey, params?: Record<string, string | number>) => string;

const PREFIX = "component.ev_charging.selector.panel.options.";

export function makeTranslate(resources: Record<string, string>): Translate {
  return (key, params) => {
    const text = resources[PREFIX + key];
    if (text === undefined) {
      return key;
    }
    if (!params) {
      return text;
    }
    return text.replace(/\{(\w+)\}/g, (placeholder, name: string) =>
      name in params ? String(params[name]) : placeholder,
    );
  };
}

const cache = new Map<string, Promise<Translate>>();

// The texts come from the integration's translation files, delivered by the
// frontend's own translation command.
export function loadTranslate(hass: HomeAssistant): Promise<Translate> {
  const language = hass.language;
  let pending = cache.get(language);
  if (pending === undefined) {
    pending = hass
      .callWS<{ resources: Record<string, string> }>({
        type: "frontend/get_translations",
        language,
        category: "selector",
        integration: ["ev_charging"],
      })
      .then((result) => makeTranslate(result.resources));
    pending.catch(() => cache.delete(language));
    cache.set(language, pending);
  }
  return pending;
}

export function clearTranslateCache(): void {
  cache.clear();
}
