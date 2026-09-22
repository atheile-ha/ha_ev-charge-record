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
