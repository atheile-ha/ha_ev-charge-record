import { LitElement, css, html, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { listSessions } from "./api";
import { onConnectionReady } from "./connection";
import { formatCost, formatEnergy, formatPercent } from "./format";
import { loadTranslate, makeTranslate, type Translate } from "./i18n";
import { monthSolarSharePercent, type LivePayload } from "./live";
import { currentYearMonth, summarizeSessions } from "./logic";
import { sharedStyles } from "./styles";
import type { HomeAssistant, Session } from "./types";

const REFRESH_INTERVAL_MS = 10 * 60 * 1000;
const LIVE_COMMAND = "ev_charging/live/subscribe";

interface MonthCardConfig {
  title?: string;
}

// Energy, cost and solar share of the current month. The month is reloaded
// when a charging session ends and otherwise every ten minutes.
export class EvChargingMonthCard extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config: MonthCardConfig = {};
  @state() private _t?: Translate;
  @state() private _sessions?: Session[];
  @state() private _failed = false;

  private _started = false;
  private _timer?: number;
  private _activeCount = 0;
  private _unsubscribe?: Promise<() => Promise<void>>;
  private _connectionUnsub?: () => void;

  public setConfig(config: MonthCardConfig): void {
    this._config = config;
  }

  public getCardSize(): number {
    return 3;
  }

  public static getStubConfig(): Record<string, unknown> {
    return {};
  }

  public override connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => {
      if (this.hass && this._started && !this._failed) {
        void this._load(this.hass, true);
      }
    }, REFRESH_INTERVAL_MS);
    if (this.hass && this._started) {
      this._watchSessions(this.hass);
    }
    if (this.hass) {
      this._watchConnection(this.hass);
    }
  }

  public override disconnectedCallback(): void {
    window.clearInterval(this._timer);
    this._release();
    this._connectionUnsub?.();
    this._connectionUnsub = undefined;
    super.disconnectedCallback();
  }

  // Home Assistant sets hass on every state change; only the first one starts the card.
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
    this._watchSessions(hass);
    await this._load(hass, false);
  }

  // Any running session ending changes the month, so it is worth a reload.
  private _watchSessions(hass: HomeAssistant): void {
    this._release();
    this._unsubscribe = hass.connection.subscribeMessage<LivePayload>(
      (blocks) => {
        const activeCount = blocks.filter((block) => block.active).length;
        if (activeCount < this._activeCount && this.hass) {
          void this._load(this.hass, true);
        }
        this._activeCount = activeCount;
      },
      { type: LIVE_COMMAND },
    );
    this._unsubscribe.catch(() => {
      this._unsubscribe = undefined;
    });
  }

  private _release(): void {
    const pending = this._unsubscribe;
    this._unsubscribe = undefined;
    pending?.then(
      (unsubscribe) => unsubscribe(),
      () => undefined,
    );
  }

  private async _load(hass: HomeAssistant, silent: boolean): Promise<void> {
    const { year, month } = currentYearMonth(new Date(), hass.config.time_zone);
    try {
      this._sessions = await listSessions(hass, { year, month });
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

  private _row(label: string, value: string): TemplateResult {
    return html`<div class="row">
      <dt>${label}</dt>
      <dd>${value}</dd>
    </div>`;
  }

  protected override render(): TemplateResult {
    const t = this._t;
    const hass = this.hass;
    if (!t || !hass) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    if (this._failed) {
      return html`<div class="message">
        <span>${t("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
      </div>`;
    }
    const locale = hass.locale?.language ?? hass.language;
    const { year, month } = currentYearMonth(new Date(), hass.config.time_zone);
    const heading =
      this._config.title ??
      new Intl.DateTimeFormat(locale, { month: "long", year: "numeric", timeZone: "UTC" }).format(
        new Date(Date.UTC(year, month - 1, 1)),
      );
    if (this._sessions === undefined) {
      return html`<h2>${heading}</h2>
        <div class="spinner" role="progressbar"></div>`;
    }
    const summary = summarizeSessions(this._sessions);
    const solar = monthSolarSharePercent(this._sessions);
    return html`
      <h2>${heading}</h2>
      <dl>
        ${this._row(t("total_energy"), formatEnergy(summary.energy_kwh, locale, summary.energy_is_estimate))}
        ${this._row(t("total_cost"), formatCost(summary.cost, locale, hass.config.currency))}
        ${this._row(t("month_solar_share"), formatPercent(solar, locale))}
      </dl>
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

      dl {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 8px 16px;
        margin: 0;
      }

      .row {
        display: flex;
        flex-direction: column;
      }

      dt {
        color: var(--ev-muted);
        font-size: 0.85em;
      }

      dd {
        margin: 0;
        font-size: 1.2em;
        font-variant-numeric: tabular-nums;
      }
    `,
  ];
}
