import { LitElement, css, html, type TemplateResult } from "lit";
import { property } from "lit/decorators.js";
import "./ev-charging-panel-view";
import { sharedStyles } from "./styles";
import type { HomeAssistant } from "./types";

// The dashboard card: the same shared view as the sidebar panel, without
// the menu button and without an address bar to mirror state into.
export class EvChargingPanelCard extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property({ type: Boolean, reflect: true, attribute: "is-panel" }) public isPanel = false;

  public setConfig(_config: Record<string, unknown>): void {
    // The card has no options.
  }

  public getCardSize(): number {
    return 8;
  }

  public getGridOptions(): Record<string, number> {
    return { columns: 12, min_columns: 6 };
  }

  public static getStubConfig(): Record<string, unknown> {
    return {};
  }

  protected override render(): TemplateResult {
    return html`<div class="card">
      <ev-charging-panel-view .hass=${this.hass}></ev-charging-panel-view>
    </div>`;
  }

  public static override styles = [
    sharedStyles,
    css`
      :host {
        display: block;
        background: var(--ha-card-background, var(--card-background-color, #fff));
        border: var(--ha-card-border-width, 1px) solid
          var(--ha-card-border-color, var(--divider-color, transparent));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, none);
      }

      :host([is-panel]) {
        height: 100%;
        overflow-y: auto;
        border: none;
        border-radius: 0;
      }

      .card {
        padding: 16px;
      }
    `,
  ];
}
