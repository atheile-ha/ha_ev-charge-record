import { describe, expect, it, vi } from "vitest";
import { onConnectionReady } from "../src/connection";
import type { HomeAssistant } from "../src/types";

function fakeHass(): { hass: HomeAssistant; fire: () => void } {
  let handler: (() => void) | undefined;
  const hass = {
    language: "de",
    locale: { language: "de" },
    config: { currency: "EUR", time_zone: "UTC" },
    callWS: vi.fn(),
    connection: {
      subscribeMessage: vi.fn(),
      addEventListener: vi.fn((type: string, listener: () => void) => {
        if (type === "ready") {
          handler = listener;
        }
      }),
      removeEventListener: vi.fn(),
    },
  } as unknown as HomeAssistant;
  return { hass, fire: () => handler?.() };
}

describe("onConnectionReady", () => {
  it("calls retry when the connection becomes ready", () => {
    const { hass, fire } = fakeHass();
    const retry = vi.fn();

    onConnectionReady(hass, retry);
    expect(retry).not.toHaveBeenCalled();

    fire();
    expect(retry).toHaveBeenCalledTimes(1);

    fire();
    expect(retry).toHaveBeenCalledTimes(2);
  });

  it("registers for the ready event specifically", () => {
    const { hass } = fakeHass();

    onConnectionReady(hass, vi.fn());

    expect(hass.connection.addEventListener).toHaveBeenCalledWith("ready", expect.any(Function));
  });

  it("returns a function that removes exactly the registered listener", () => {
    const { hass } = fakeHass();

    const stop = onConnectionReady(hass, vi.fn());
    stop();

    const [type, listener] = (
      hass.connection.addEventListener as unknown as { mock: { calls: [string, () => void][] } }
    ).mock.calls[0];
    expect(hass.connection.removeEventListener).toHaveBeenCalledWith(type, listener);
  });
});
