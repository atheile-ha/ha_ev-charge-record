import { EvChargingLiveCard } from "./ev-charging-live-card";
import { EvChargingMonthCard } from "./ev-charging-month-card";
import { EvChargingPanel } from "./ev-charging-panel";
import { EvChargingPanelCard } from "./ev-charging-panel-card";
import { EvChargingPanelView } from "./ev-charging-panel-view";
import { EvChargingRecentCard, EvChargingRecentCardEditor } from "./ev-charging-recent-card";
import { EvChargingSessionList } from "./ev-charging-session-list";

function defineOnce(name: string, constructor: CustomElementConstructor): void {
  if (!customElements.get(name)) {
    customElements.define(name, constructor);
  }
}

defineOnce("ev-charging-panel-view", EvChargingPanelView);
defineOnce("ev-charging-session-list", EvChargingSessionList);
defineOnce("ev-charging-panel", EvChargingPanel);
defineOnce("ev-charging-panel-card", EvChargingPanelCard);
defineOnce("ev-charging-recent-card", EvChargingRecentCard);
defineOnce("ev-charging-recent-card-editor", EvChargingRecentCardEditor);
defineOnce("ev-charging-live-card", EvChargingLiveCard);
defineOnce("ev-charging-month-card", EvChargingMonthCard);

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
