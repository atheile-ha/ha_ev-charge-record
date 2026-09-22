import { LitElement, css, html, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { listSessions } from "./api";
import { onConnectionReady } from "./connection";
import "./ev-charging-session-list";
import { loadTranslate, makeTranslate, type Translate } from "./i18n";
import { sharedStyles } from "./styles";
import type { HomeAssistant, Session } from "./types";

const DEFAULT_COUNT = 3;
const MAX_COUNT = 20;
const REFRESH_INTERVAL_MS = 10 * 60 * 1000;

interface RecentCardConfig {
  count?: number;
  title?: string;
}

function isValidCount(count: number): boolean {
  return Number.isInteger(count) && count >= 1 && count <= MAX_COUNT;
}

export class EvChargingRecentCard extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config: RecentCardConfig = {};
  @state() private _t?: Translate;
  @state() private _sessions?: Session[];
  @state() private _failed = false;

  private _started = false;
  private _timer?: number;
  private _connectionUnsub?: () => void;

  public setConfig(config: RecentCardConfig): void {
    if (!isValidCount(config.count ?? DEFAULT_COUNT)) {
      throw new Error(`count must be a whole number from 1 to ${MAX_COUNT}`);
    }
    this._config = config;
    if (this._started && this.hass) {
      void this._load(this.hass, true);
    }
  }

  public getCardSize(): number {
    return 1 + (this._config.count ?? DEFAULT_COUNT) * 2;
  }

  public static getStubConfig(): Record<string, unknown> {
    return { count: DEFAULT_COUNT };
  }

  public static getConfigElement(): HTMLElement {
    return document.createElement("ev-charging-recent-card-editor");
  }

  public override connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => {
      if (this.hass && this._started && !this._failed) {
        void this._load(this.hass, true);
      }
    }, REFRESH_INTERVAL_MS);
    if (this.hass) {
      this._watchConnection(this.hass);
    }
  }

  public override disconnectedCallback(): void {
    window.clearInterval(this._timer);
    this._connectionUnsub?.();
    this._connectionUnsub = undefined;
    super.disconnectedCallback();
  }

  // Home Assistant sets hass on every state change; only the first one loads.
  protected override shouldUpdate(changed: PropertyValues): boolean {
    const onlyHass = changed.size === 1 && changed.has("hass");
    return !(onlyHass && this._started);
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (changed.has("hass") && this.hass && !this._started) {
      this._started = true;
      void this._start(this.hass);
      this._watchConnection(this.hass);
    }
  }

  // A load that raced a reconnect leaves the card failed; retry once the
  // connection is back instead of waiting only for a manual click.
  private _watchConnection(hass: HomeAssistant): void {
    if (this._connectionUnsub) {
      return;
    }
    this._connectionUnsub = onConnectionReady(hass, () => {
      if (this._failed) {
        this._retry();
      }
    });
  }

  private async _start(hass: HomeAssistant): Promise<void> {
    try {
      this._t = await loadTranslate(hass);
    } catch (error) {
      console.error("ev_charging: loading translations failed", error);
      this._t = makeTranslate({});
      this._failed = true;
      return;
    }
    await this._load(hass, false);
  }

  private async _load(hass: HomeAssistant, silent: boolean): Promise<void> {
    try {
      this._sessions = await listSessions(hass, { limit: this._config.count ?? DEFAULT_COUNT });
      this._failed = false;
    } catch (error) {
      console.error("ev_charging: loading sessions failed", error);
      if (!silent) {
        this._failed = true;
      }
    }
  }

  private _retry(): void {
    if (this.hass) {
      this._failed = false;
      this._started = false;
      this.requestUpdate();
    }
  }

  protected override render(): TemplateResult {
    const t = this._t;
    if (!t || !this.hass) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    if (this._failed) {
      return html`<div class="message">
        <span>${t("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
      </div>`;
    }
    return html`
      <h2>${this._config.title ?? t("recent_title")}</h2>
      ${this._sessions === undefined
        ? html`<div class="spinner" role="progressbar"></div>`
        : this._sessions.length === 0
          ? html`<div class="message">${t("no_sessions")}</div>`
          : html`<ev-charging-session-list
              .hass=${this.hass}
              .t=${t}
              .sessions=${this._sessions}
            ></ev-charging-session-list>`}
    `;
  }

  public static override styles = [
    sharedStyles,
    css`
      :host {
        display: block;
        padding: 16px;
        background: var(--ha-card-background, var(--card-background-color, #fff));
        border: var(--ha-card-border-width, 1px) solid
          var(--ha-card-border-color, var(--divider-color, transparent));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, none);
      }

      h2 {
        margin: 0 0 8px;
        font-size: 1.1em;
        font-weight: 500;
      }
    `,
  ];
}

// The visual editor of the card in the dashboard editor.
export class EvChargingRecentCardEditor extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config: RecentCardConfig = {};
  @state() private _t?: Translate;

  private _started = false;

  public setConfig(config: RecentCardConfig): void {
    this._config = config;
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (changed.has("hass") && this.hass && !this._started) {
      this._started = true;
      loadTranslate(this.hass).then(
        (t) => (this._t = t),
        () => (this._t = makeTranslate({})),
      );
    }
  }

  private _changed(event: Event): void {
    const count = Number((event.target as HTMLInputElement).value);
    if (!isValidCount(count)) {
      (event.target as HTMLInputElement).value = String(this._config.count ?? DEFAULT_COUNT);
      return;
    }
    this._config = { ...this._config, count };
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      }),
    );
  }

  protected override render(): TemplateResult {
    const t = this._t;
    if (!t) {
      return html``;
    }
    return html`<label>
      <span>${t("card_count")}</span>
      <input
        type="number"
        min="1"
        max=${MAX_COUNT}
        step="1"
        .value=${String(this._config.count ?? DEFAULT_COUNT)}
        @change=${(event: Event) => this._changed(event)}
      />
    </label>`;
  }

  public static override styles = [
    sharedStyles,
    css`
      label {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }

      input {
        width: 80px;
        padding: 6px 8px;
        font: inherit;
        color: inherit;
        background: var(--ev-surface);
        border: 1px solid var(--ev-line);
        border-radius: 8px;
      }
    `,
  ];
}
