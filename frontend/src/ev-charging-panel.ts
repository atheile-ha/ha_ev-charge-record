import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { property } from "lit/decorators.js";
import "./ev-charging-panel-view";
import { parseState, serializeState, type PanelState } from "./logic";
import { sharedStyles } from "./styles";
import type { HomeAssistant } from "./types";

const MENU = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";

interface PanelInfo {
  title?: string;
  url_path?: string;
}

// The sidebar panel: a thin shell around the shared view. It adds the menu
// button and mirrors the view state into the address bar.
export class EvChargingPanel extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property({ type: Boolean }) public narrow = false;
  @property({ attribute: false }) public route?: { prefix: string; path: string };
  @property({ attribute: false }) public panel?: PanelInfo;

  private _initialState?: Partial<PanelState>;

  protected override willUpdate(): void {
    if (this._initialState === undefined) {
      this._initialState = parseState(this.route?.path ?? "", window.location.search);
    }
  }

  private _toggleMenu(): void {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
  }

  private _onStateChanged(event: CustomEvent<PanelState>): void {
    const prefix = this.route?.prefix ?? `/${this.panel?.url_path ?? ""}`;
    window.history.replaceState(window.history.state, "", `${prefix}${serializeState(event.detail)}`);
  }

  protected override render(): TemplateResult {
    return html`
      <header>
        ${this.narrow
          ? html`<button class="menu" @click=${() => this._toggleMenu()}>
              <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                <path d=${MENU} fill="currentColor"></path>
              </svg>
            </button>`
          : nothing}
        <h1>${this.panel?.title ?? ""}</h1>
      </header>
      <main>
        <ev-charging-panel-view
          .hass=${this.hass}
          .initialState=${this._initialState}
          @ev-state-changed=${this._onStateChanged}
        ></ev-charging-panel-view>
      </main>
    `;
  }

  public static override styles = [
    sharedStyles,
    css`
      :host {
        display: block;
        height: 100%;
        overflow-y: auto;
        background: var(--primary-background-color);
      }

      header {
        position: sticky;
        top: 0;
        z-index: 1;
        display: flex;
        align-items: center;
        gap: 8px;
        height: 56px;
        padding: 0 16px;
        background: var(--app-header-background-color, var(--primary-color));
        color: var(--app-header-text-color, #fff);
      }

      h1 {
        margin: 0;
        font-size: 1.25em;
        font-weight: 400;
      }

      button.menu {
        display: inline-flex;
        padding: 8px;
        margin-left: -8px;
        background: transparent;
        border: none;
        border-radius: 50%;
        color: inherit;
        cursor: pointer;
      }

      main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 16px;
      }
    `,
  ];
}
