import type { HomeAssistant } from "./types";

// Retries once the websocket connection is (re-)established, so a card stuck
// in an error state from a load that raced a reconnect recovers on its own
// instead of only through a manual click. Returns the function that stops
// watching; call it when the element leaves the DOM.
export function onConnectionReady(hass: HomeAssistant, retry: () => void): () => void {
  const handler = (): void => retry();
  hass.connection.addEventListener("ready", handler);
  return () => hass.connection.removeEventListener("ready", handler);
}

// What a view has loaded so far: the year whose sessions it holds, and
// whether it holds the open sessions.
export interface LoadedData {
  started: boolean;
  failed: boolean;
  year?: number;
  open: boolean;
}

export type ReconnectPlan =
  | { kind: "none" }
  | { kind: "retry" }
  | { kind: "reload"; year?: number; open: boolean };

// After the connection is back, Home Assistant may have restarted with other
// data. A failed view starts over; otherwise everything loaded so far, the
// shown view and the cached ones, is fetched again.
export function reconnectPlan(loaded: LoadedData): ReconnectPlan {
  if (loaded.failed) {
    return { kind: "retry" };
  }
  if (!loaded.started) {
    return { kind: "none" };
  }
  return { kind: "reload", year: loaded.year, open: loaded.open };
}
