import { LitElement, css, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { listSessions } from "./api";
import { formatCost, formatDateTime, formatDuration, formatEnergy, formatPercent } from "./format";
import { loadTranslate, makeTranslate, type Translate } from "./i18n";
import { vehicleLabel } from "./labels";
import { sharedStyles } from "./styles";
import type { HomeAssistant, Session } from "./types";

const DEFAULT_COUNT = 3;
const MAX_COUNT = 20;
const REFRESH_INTERVAL_MS = 10 * 60 * 1000;

interface RecentCardConfig {
  count?: number;
  title?: string;
}

export class EvChargingRecentCard extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config: RecentCardConfig = {};
  @state() private _t?: Translate;
  @state() private _sessions?: Session[];
  @state() private _failed = false;

  private _started = false;
  private _timer?: number;

  public setConfig(config: RecentCardConfig): void {
    const count = config.count ?? DEFAULT_COUNT;
    if (!Number.isInteger(count) || count < 1 || count > MAX_COUNT) {
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

  public override connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => {
      if (this.hass && this._started && !this._failed) {
        void this._load(this.hass, true);
      }
    }, REFRESH_INTERVAL_MS);
  }

  public override disconnectedCallback(): void {
    window.clearInterval(this._timer);
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
    }
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
    const title = this._config.title ?? t("recent_title");
    if (this._failed) {
      return html`<div class="message">
        <span>${t("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
      </div>`;
    }
    return html`
      <h2>${title}</h2>
      ${this._sessions === undefined
        ? html`<div class="spinner" role="progressbar"></div>`
        : this._sessions.length === 0
          ? html`<div class="message">${t("no_sessions")}</div>`
          : html`<ul>
              ${this._sessions.map((session) => this._renderSession(session, t))}
            </ul>`}
    `;
  }

  private _renderSession(session: Session, t: Translate): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const soc =
      session.soc_start !== null && session.soc_end !== null
        ? `${formatPercent(session.soc_start, locale)} → ${formatPercent(session.soc_end, locale)}`
        : nothing;
    return html`<li>
      <div class="line">
        <span class=${classMap({ vehicle: true, unassigned: session.vehicle_id === null })}
          >${vehicleLabel(session, t)}</span
        >
        <span class="muted">${formatDateTime(session.plug_start, locale, hass.config.time_zone)}</span>
      </div>
      <div class="line">
        <span>
          ${formatEnergy(session.energy_kwh, locale, session.energy_is_estimate)} ·
          ${formatCost(session.cost, locale, hass.config.currency)} ·
          ${formatDuration(session.charge_duration_min)}
        </span>
        <span class="muted">${soc}</span>
      </div>
      <div class="line">
        <span class="chip">${t(`location_${session.location}`)}</span>
        ${session.status === "complete"
          ? nothing
          : html`<span class="chip warn">${t(`status_${session.status}`)}</span>`}
      </div>
    </li>`;
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

      ul {
        display: flex;
        flex-direction: column;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      li {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 10px 0;
      }

      li + li {
        border-top: 1px solid var(--ev-line);
      }

      .line {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 4px 12px;
      }

      .vehicle {
        font-weight: 500;
      }
    `,
  ];
}
