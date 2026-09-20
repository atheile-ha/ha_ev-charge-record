import { LitElement, css, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import {
  formatCost,
  formatDuration,
  formatEnergy,
  formatPercent,
  formatPower,
  formatPricePerKwh,
  formatTime,
} from "./format";
import { loadTranslate, makeTranslate, type TextKey, type Translate } from "./i18n";
import {
  assignmentText,
  counterText,
  dataGaps,
  idleText,
  netDurationMinutes,
  phasesText,
  plugDurationMinutes,
  plugText,
  readingText,
  solarSharePercent,
  stateText,
  unallocatedText,
  vehicleText,
  type LiveFormat,
  type LivePayload,
} from "./live";
import { sharedStyles } from "./styles";
import type { HomeAssistant } from "./types";

const LIVE_COMMAND = "ev_charging/live/subscribe";
const TICK_MS = 1000;

interface LiveCardConfig {
  title?: string;
}

interface WebSocketError {
  code?: string;
}

// The running session. The values come from the server over a subscription,
// so the card follows the source entities instead of the entity publish interval.
export class EvChargingLiveCard extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config: LiveCardConfig = {};
  @state() private _t?: Translate;
  @state() private _live?: LivePayload;
  @state() private _received = 0;
  @state() private _now = Date.now();
  @state() private _failed = false;
  @state() private _noWallbox = false;

  private _started = false;
  private _unsubscribe?: Promise<() => Promise<void>>;
  private _timer?: number;

  public setConfig(config: LiveCardConfig): void {
    this._config = config;
  }

  public getCardSize(): number {
    return 5;
  }

  public static getStubConfig(): Record<string, unknown> {
    return {};
  }

  public override connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => {
      if (this._live?.active) {
        this._now = Date.now();
      }
    }, TICK_MS);
    if (this.hass && this._started) {
      void this._subscribe(this.hass);
    }
  }

  public override disconnectedCallback(): void {
    window.clearInterval(this._timer);
    this._release();
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
    }
  }

  private async _start(hass: HomeAssistant): Promise<void> {
    try {
      this._t = await loadTranslate(hass);
    } catch (error) {
      console.error("ev_charging: loading translations failed", error);
      this._t = makeTranslate({});
    }
    await this._subscribe(hass);
  }

  private async _subscribe(hass: HomeAssistant): Promise<void> {
    this._release();
    this._failed = false;
    this._noWallbox = false;
    const pending = hass.connection.subscribeMessage<LivePayload>(
      (payload) => {
        this._live = payload;
        this._received = Date.now();
        this._now = this._received;
      },
      { type: LIVE_COMMAND },
    );
    this._unsubscribe = pending;
    try {
      await pending;
    } catch (error) {
      this._unsubscribe = undefined;
      if ((error as WebSocketError).code === "not_found") {
        this._noWallbox = true;
      } else {
        console.error("ev_charging: subscribing to the live values failed", error);
        this._failed = true;
      }
    }
  }

  private _release(): void {
    const pending = this._unsubscribe;
    this._unsubscribe = undefined;
    pending?.then(
      (unsubscribe) => unsubscribe(),
      () => undefined,
    );
  }

  private _retry(): void {
    if (this.hass) {
      void this._subscribe(this.hass);
    }
  }

  private _row(label: string, value: string): TemplateResult {
    return html`<div class="row">
      <dt>${label}</dt>
      <dd>${value}</dd>
    </div>`;
  }

  private _vehicle(live: LivePayload, t: Translate): TemplateResult {
    const unassigned = !live.vehicle_guest && live.vehicle === null;
    return html`<div class="vehicle ${unassigned ? "unassigned" : ""}">${vehicleText(live, t)}</div>`;
  }

  private _format(hass: HomeAssistant): LiveFormat {
    return {
      locale: hass.locale?.language ?? hass.language,
      timeZone: hass.config.time_zone,
      now: this._now,
    };
  }

  // The state of the session and where it came from: what it is doing, the plug,
  // the assignment and the reading of the identification.
  private _status(live: LivePayload, t: Translate, format: LiveFormat): TemplateResult {
    const phases = phasesText(live, t);
    const lines = [
      assignmentText(live, t),
      plugText(live, t, format),
      readingText(live, t),
    ].filter((line): line is string => line !== null);
    return html`<div class="status">
      <div class="state">
        ${stateText(live, t, format)}${phases === null ? nothing : html` · ${phases}`}
      </div>
      ${lines.map((line) => html`<div class="line">${line}</div>`)}
    </div>`;
  }

  // The data situation: which counter carries the energy, and energy that could
  // not be assigned.
  private _situation(
    live: LivePayload,
    t: Translate,
    locale: string,
  ): TemplateResult | typeof nothing {
    const lines = [counterText(live, t), unallocatedText(live, t, locale)].filter(
      (line): line is string => line !== null,
    );
    return lines.length === 0
      ? nothing
      : html`<div class="situation">${lines.map((line) => html`<div>${line}</div>`)}</div>`;
  }

  private _soc(live: LivePayload, t: Translate, locale: string): TemplateResult | typeof nothing {
    if (live.soc_start === null && live.soc === null) {
      return nothing;
    }
    const range =
      live.soc_start !== null && live.soc !== null
        ? `${formatPercent(live.soc_start, locale)} → ${formatPercent(live.soc, locale)}`
        : formatPercent(live.soc ?? live.soc_start, locale);
    const target =
      live.soc_target === null ? "" : ` (${t("live_soc_target", { target: live.soc_target })})`;
    return this._row(t("live_soc"), `${range}${target}`);
  }

  private _flags(live: LivePayload, t: Translate): TemplateResult | typeof nothing {
    const flags: TemplateResult[] = [];
    if (live.charge_error) {
      flags.push(html`<span class="chip alert">${t("flag_charge_error")}</span>`);
    }
    if (live.location_conflict) {
      flags.push(html`<span class="chip warn">${t("flag_location_conflict")}</span>`);
    }
    if (live.identification_conflict) {
      flags.push(html`<span class="chip warn">${t("flag_identification_conflict")}</span>`);
    }
    if (live.flagged) {
      flags.push(html`<span class="chip warn">${t("status_flagged")}</span>`);
    }
    return flags.length === 0 ? nothing : html`<div class="flags">${flags}</div>`;
  }

  private _details(live: LivePayload, t: Translate, hass: HomeAssistant): TemplateResult {
    const locale = hass.locale?.language ?? hass.language;
    const currency = live.currency || hass.config.currency;
    const solar = solarSharePercent(live);
    const gaps = dataGaps(live, t);
    const split =
      live.energy_grid_kwh === null || live.energy_solar_kwh === null
        ? gaps.split === null
          ? nothing
          : this._row(`${t("detail_energy_grid")} / ${t("detail_energy_solar")}`, gaps.split)
        : this._row(
            `${t("detail_energy_grid")} / ${t("detail_energy_solar")}`,
            `${formatEnergy(live.energy_grid_kwh, locale)} / ${formatEnergy(
              live.energy_solar_kwh,
              locale,
            )}${solar === null ? "" : ` (${t("live_solar_share", { percent: Math.round(solar) })})`}`,
          );
    const price =
      live.effective_price === null
        ? nothing
        : this._row(
            t("live_price"),
            formatPricePerKwh(live.effective_price, locale, currency),
          );
    const end =
      live.charge_end === null
        ? nothing
        : this._row(t("live_charge_end"), formatTime(live.charge_end, locale, hass.config.time_zone));
    return html`<dl>
      ${this._soc(live, t, locale)}
      ${this._row(t("live_power"), formatPower(live.charge_power_kw, locale))}
      ${this._row(t("live_energy"), formatEnergy(live.energy_kwh, locale))} ${split}
      ${this._row(t("live_cost"), gaps.cost ?? formatCost(live.cost, locale, currency))} ${price}
      ${this._row(
        t("live_charge_time"),
        formatDuration(netDurationMinutes(live, this._received, this._now)),
      )}
      ${this._row(t("live_plug_time"), formatDuration(plugDurationMinutes(live, this._now)))}
      ${end}
    </dl>`;
  }

  protected override render(): TemplateResult {
    const t = this._t;
    const hass = this.hass;
    if (!t || !hass) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    const title = this._config.title ?? t("live_title");
    if (this._noWallbox) {
      return html`<h2>${title}</h2>
        <div class="message">${t("live_no_wallbox")}</div>`;
    }
    if (this._failed) {
      return html`<h2>${title}</h2>
        <div class="message">
          <span>${t("load_error")}</span>
          <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
        </div>`;
    }
    const live = this._live;
    if (live === undefined) {
      return html`<h2>${title}</h2>
        <div class="spinner" role="progressbar"></div>`;
    }
    if (!live.active) {
      return html`<h2>${title}</h2>
        <div class="message">${idleText(live, t)}</div>`;
    }
    const stateKey = `live_state_${live.state}` as TextKey;
    return html`
      <h2>
        <span>${title}</span>
        <span class="chip ${live.state === "error" ? "alert" : ""}"
          >${t(stateKey)}</span
        >
      </h2>
      ${this._vehicle(live, t)} ${this._status(live, t, this._format(hass))}
      ${this._details(live, t, hass)}
      ${this._situation(live, t, hass.locale?.language ?? hass.language)} ${this._flags(live, t)}
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
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin: 0 0 8px;
        font-size: 1.1em;
        font-weight: 500;
      }

      .vehicle {
        margin-bottom: 8px;
        font-size: 1.3em;
        font-weight: 500;
      }

      .status {
        margin-bottom: 12px;
      }

      .status .state {
        font-weight: 500;
      }

      .status .line,
      .situation {
        color: var(--ev-muted);
        font-size: 0.9em;
      }

      .situation {
        margin-top: 12px;
      }

      dl {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
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
        font-variant-numeric: tabular-nums;
      }

      .flags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 12px;
      }
    `,
  ];
}
