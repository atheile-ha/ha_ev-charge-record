import { EvChargingLiveCard } from "./ev-charging-live-card";
import { EvChargingMonthCard } from "./ev-charging-month-card";
import { EvChargingPanel } from "./ev-charging-panel";
import { EvChargingPanelCard } from "./ev-charging-panel-card";
import { EvChargingPanelView } from "./ev-charging-panel-view";
import { EvChargingRecentCard, EvChargingRecentCardEditor } from "./ev-charging-recent-card";
import { EvChargingSessionList } from "./ev-charging-session-list";
import { keepDefined } from "./registry";

keepDefined(
  [
    ["ev-charging-panel-view", EvChargingPanelView],
    ["ev-charging-session-list", EvChargingSessionList],
    ["ev-charging-panel", EvChargingPanel],
    ["ev-charging-panel-card", EvChargingPanelCard],
    ["ev-charging-recent-card", EvChargingRecentCard],
    ["ev-charging-recent-card-editor", EvChargingRecentCardEditor],
    ["ev-charging-live-card", EvChargingLiveCard],
    ["ev-charging-month-card", EvChargingMonthCard],
  ],
  {
    onIncomplete: () =>
      console.warn("ev_charging: the element registry of this page refuses the cards"),
  },
);

// Makes the cards appear in the dashboard card picker. The picker reads the
// name before any translation is available, so it shows the card type.
interface CustomCardEntry {
  type: string;
  name: string;
}
const registry = window as unknown as { customCards?: CustomCardEntry[] };
registry.customCards = registry.customCards ?? [];
for (const type of [
  "ev-charging-panel-card",
  "ev-charging-recent-card",
  "ev-charging-live-card",
  "ev-charging-month-card",
]) {
  if (!registry.customCards.some((entry) => entry.type === type)) {
    registry.customCards.push({ type, name: type });
  }
}
