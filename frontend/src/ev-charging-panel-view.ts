import { LitElement, css, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { getStats, listSessions, listVehicles } from "./api";
import {
  EMPTY,
  formatCost,
  formatDateTime,
  formatDistance,
  formatDuration,
  formatEnergy,
  formatPercent,
  formatPower,
  formatTime,
  monthName,
} from "./format";
import { loadTranslate, makeTranslate, type TextKey, type Translate } from "./i18n";
import { fieldLabel, vehicleLabel } from "./labels";
import {
  EMPTY_FILTERS,
  NO_CARD,
  UNASSIGNED,
  applyFilters,
  cardOptions,
  currentYearMonth,
  defaultState,
  hasActiveFilter,
  shiftMonth,
  vehicleOptions,
  yearOptions,
  type Filters,
  type Option,
  type PanelState,
  type ViewId,
} from "./logic";
import { sharedStyles } from "./styles";
import type {
  ChargeType,
  HomeAssistant,
  MonthStats,
  Session,
  SessionLocation,
  SessionStatus,
  StatsResponse,
  Summary,
  Vehicle,
} from "./types";

const REFRESH_INTERVAL_MS = 10 * 60 * 1000;
const RECENT_COUNT = 5;

const CHEVRON_LEFT = "M15.41,16.58L10.83,12L15.41,7.42L14,6L8,12L14,18L15.41,16.58Z";
const CHEVRON_RIGHT = "M8.59,16.58L13.17,12L8.59,7.42L10,6L16,12L10,18L8.59,16.58Z";

const VIEWS: { id: ViewId; label: TextKey }[] = [
  { id: "overview", label: "view_overview" },
  { id: "detail", label: "view_detail" },
  { id: "recent", label: "view_recent" },
];
const LOCATIONS: SessionLocation[] = ["home", "home_no_wallbox", "external"];
const CHARGE_TYPES: ChargeType[] = ["ac", "dc", "unknown"];
const STATUSES: SessionStatus[] = ["complete", "followup_open", "flagged"];

type Metric = "energy" | "cost" | "duration";
const METRICS: { id: Metric; label: TextKey }[] = [
  { id: "energy", label: "total_energy" },
  { id: "cost", label: "total_cost" },
  { id: "duration", label: "total_duration" },
];

function icon(path: string): TemplateResult {
  return html`<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
    <path d=${path} fill="currentColor"></path>
  </svg>`;
}

// The shared body of the panel and of ev-charging-panel-card. It does not know
// which of the two it sits in; both pass the same properties and listen for
// the same event.
export class EvChargingPanelView extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property({ attribute: false }) public initialState?: Partial<PanelState>;

  @state() private _state?: PanelState;
  @state() private _t?: Translate;
  @state() private _stats?: StatsResponse;
  @state() private _sessions?: Session[];
  @state() private _recent?: Session[];
  @state() private _vehicles: Vehicle[] = [];
  @state() private _failed = false;
  @state() private _metric: Metric = "energy";

  private _started = false;
  private _statsKey?: number;
  private _sessionsKey?: string;
  private _recentRequested = false;
  private _timer?: number;

  public override connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => this._refresh(), REFRESH_INTERVAL_MS);
  }

  public override disconnectedCallback(): void {
    window.clearInterval(this._timer);
    super.disconnectedCallback();
  }

  protected override shouldUpdate(changed: PropertyValues): boolean {
    const onlyHass = changed.size === 1 && changed.has("hass");
    return !(onlyHass && this._state !== undefined);
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (changed.has("hass") && this.hass && this._state === undefined) {
      const initial = this.initialState;
      this._state = {
        ...defaultState(new Date(), this.hass.config.time_zone),
        ...initial,
        filters: { ...EMPTY_FILTERS, ...initial?.filters },
      };
    }
    this._sync();
  }

  private _sync(): void {
    const hass = this.hass;
    const state = this._state;
    if (!hass || !state) {
      return;
    }
    if (!this._started) {
      this._started = true;
      void this._loadShared(hass, false);
    }
    if (state.view !== "recent" && this._statsKey !== state.year) {
      this._statsKey = state.year;
      this._stats = undefined;
      void this._loadStats(hass, state.year, false);
    }
    if (state.view === "detail") {
      const key = `${state.year}-${state.month}`;
      if (this._sessionsKey !== key) {
        this._sessionsKey = key;
        this._sessions = undefined;
        void this._loadSessions(hass, state.year, state.month, false);
      }
    }
    if (state.view === "recent" && !this._recentRequested) {
      this._recentRequested = true;
      void this._loadRecent(hass, false);
    }
  }

  private _refresh(): void {
    const hass = this.hass;
    const state = this._state;
    if (!hass || !state || !this._started || this._failed) {
      return;
    }
    void this._loadShared(hass, true);
    if (state.view !== "recent") {
      void this._loadStats(hass, state.year, true);
    }
    if (state.view === "detail") {
      void this._loadSessions(hass, state.year, state.month, true);
    }
    if (state.view === "recent") {
      void this._loadRecent(hass, true);
    }
  }

  private _fail(error: unknown, silent: boolean): void {
    console.error("ev_charging: loading data failed", error);
    if (!silent) {
      this._failed = true;
    }
  }

  private _retry(): void {
    this._failed = false;
    this._started = false;
    this._statsKey = undefined;
    this._sessionsKey = undefined;
    this._recentRequested = false;
    this.requestUpdate();
  }

  private async _loadShared(hass: HomeAssistant, silent: boolean): Promise<void> {
    try {
      this._t = await loadTranslate(hass);
    } catch (error) {
      this._t = makeTranslate({});
      this._fail(error, silent);
      return;
    }
    try {
      this._vehicles = await listVehicles(hass);
    } catch (error) {
      this._fail(error, silent);
    }
  }

  private async _loadStats(hass: HomeAssistant, year: number, silent: boolean): Promise<void> {
    try {
      const stats = await getStats(hass, year);
      if (this._statsKey === year) {
        this._stats = stats;
      }
    } catch (error) {
      if (this._statsKey === year) {
        this._fail(error, silent);
      }
    }
  }

  private async _loadSessions(
    hass: HomeAssistant,
    year: number,
    month: number,
    silent: boolean,
  ): Promise<void> {
    const key = `${year}-${month}`;
    try {
      const sessions = await listSessions(hass, { year, month });
      if (this._sessionsKey === key) {
        this._sessions = sessions;
      }
    } catch (error) {
      if (this._sessionsKey === key) {
        this._fail(error, silent);
      }
    }
  }

  private async _loadRecent(hass: HomeAssistant, silent: boolean): Promise<void> {
    try {
      this._recent = await listSessions(hass, { limit: RECENT_COUNT });
    } catch (error) {
      this._fail(error, silent);
    }
  }

  private _setState(patch: Partial<PanelState>): void {
    if (!this._state) {
      return;
    }
    this._state = { ...this._state, ...patch };
    this.dispatchEvent(new CustomEvent("ev-state-changed", { detail: this._state }));
  }

  private _setFilter(key: keyof Filters, value: string): void {
    if (this._state) {
      this._setState({ filters: { ...this._state.filters, [key]: value } });
    }
  }

  private _shift(delta: number): void {
    if (this._state) {
      this._setState(shiftMonth(this._state.year, this._state.month, delta));
    }
  }

  protected override render(): TemplateResult | typeof nothing {
    const state = this._state;
    if (!state || !this.hass) {
      return nothing;
    }
    if (this._failed) {
      return this._renderError(this._t ?? makeTranslate({}));
    }
    const t = this._t;
    if (!t) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    return html`
      <div class="view">
        ${this._renderTabs(t, state)}
        ${state.view === "recent" ? nothing : this._renderPeriod(t, state)}
        ${state.view === "overview"
          ? this._renderOverview(t, state)
          : state.view === "detail"
            ? this._renderDetail(t, state)
            : this._renderRecent(t)}
        <p class="hint muted">${t("multi_day_hint")} ${t("estimate_hint")}</p>
      </div>
    `;
  }

  private _renderError(t: Translate): TemplateResult {
    return html`<div class="message">
      <span>${t("load_error")}</span>
      <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
    </div>`;
  }

  private _renderTabs(t: Translate, state: PanelState): TemplateResult {
    return html`<nav class="tabs">
      ${VIEWS.map(
        (view) => html`<button
          class=${classMap({ tab: true, active: view.id === state.view })}
          aria-current=${view.id === state.view ? "page" : "false"}
          @click=${() => this._setState({ view: view.id })}
        >
          ${t(view.label)}
        </button>`,
      )}
    </nav>`;
  }

  private _renderPeriod(t: Translate, state: PanelState): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const current = currentYearMonth(new Date(), hass.config.time_zone);
    const years = yearOptions(this._stats?.years ?? [], current.year, state.year);
    return html`<div class="period">
      <button class="icon" aria-label=${t("period_previous")} @click=${() => this._shift(-1)}>
        ${icon(CHEVRON_LEFT)}
      </button>
      <select
        aria-label=${t("period_month")}
        @change=${(event: Event) =>
          this._setState({ month: Number((event.target as HTMLSelectElement).value) })}
      >
        ${Array.from({ length: 12 }, (_, index) => index + 1).map(
          (month) =>
            html`<option value=${month} .selected=${month === state.month}>
              ${monthName(month, locale, "long")}
            </option>`,
        )}
      </select>
      <select
        aria-label=${t("period_year")}
        @change=${(event: Event) =>
          this._setState({ year: Number((event.target as HTMLSelectElement).value) })}
      >
        ${years.map(
          (year) => html`<option value=${year} .selected=${year === state.year}>${year}</option>`,
        )}
      </select>
      <button class="icon" aria-label=${t("period_next")} @click=${() => this._shift(1)}>
        ${icon(CHEVRON_RIGHT)}
      </button>
    </div>`;
  }

  private _renderTiles(t: Translate, month: MonthStats): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const tiles: [TextKey, string][] = [
      ["total_energy", formatEnergy(month.energy_kwh, locale, month.energy_is_estimate)],
      ["total_cost", formatCost(month.cost, locale, hass.config.currency)],
      ["total_duration", formatDuration(month.charge_duration_min)],
      ["total_sessions", String(month.count)],
      ["open_followups", String(month.open_followups)],
    ];
    return html`<div class="tiles">
      ${tiles.map(
        ([label, value]) => html`<div class="tile">
          <span class="tile-label muted">${t(label)}</span>
          <span class="tile-value">${value}</span>
        </div>`,
      )}
    </div>`;
  }

  private _renderOverview(t: Translate, state: PanelState): TemplateResult {
    const stats = this._stats;
    if (!stats) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    return html`
      ${this._renderTiles(t, stats.months[state.month - 1])}
      ${this._renderChart(t, state, stats)} ${this._renderYearSummary(t, state, stats)}
    `;
  }

  private _metricValue(month: MonthStats): number {
    switch (this._metric) {
      case "cost":
        return month.cost;
      case "duration":
        return month.charge_duration_min;
      default:
        return month.energy_kwh;
    }
  }

  private _formatMetric(month: MonthStats): string {
    const hass = this.hass!;
    const locale = hass.locale.language;
    switch (this._metric) {
      case "cost":
        return formatCost(month.cost, locale, hass.config.currency);
      case "duration":
        return formatDuration(month.charge_duration_min);
      default:
        return formatEnergy(month.energy_kwh, locale, month.energy_is_estimate);
    }
  }

  private _renderChart(t: Translate, state: PanelState, stats: StatsResponse): TemplateResult {
    const locale = this.hass!.locale.language;
    const maximum = Math.max(...stats.months.map((month) => this._metricValue(month)), 0);
    return html`<section class="chart">
      <div class="chart-head">
        <h3>${t("chart_title", { year: state.year })}</h3>
        <label class="metric">
          <span class="muted">${t("chart_metric")}</span>
          <select
            @change=${(event: Event) => {
              this._metric = (event.target as HTMLSelectElement).value as Metric;
            }}
          >
            ${METRICS.map(
              (metric) =>
                html`<option value=${metric.id} .selected=${metric.id === this._metric}>
                  ${t(metric.label)}
                </option>`,
            )}
          </select>
        </label>
      </div>
      <div class="plot">
        ${stats.months.map((month) => {
          const share = maximum > 0 ? (this._metricValue(month) / maximum) * 100 : 0;
          const name = monthName(month.month, locale, "long");
          const value = month.count === 0 ? EMPTY : this._formatMetric(month);
          return html`<button
            class=${classMap({ bar: true, selected: month.month === state.month })}
            title=${`${name}: ${value}`}
            aria-label=${`${name}: ${value}`}
            aria-pressed=${month.month === state.month ? "true" : "false"}
            @click=${() => this._setState({ month: month.month })}
          >
            <span class="fill-area"><span class="fill" style=${`height:${share}%`}></span></span>
            <span class="bar-label muted">${monthName(month.month, locale, "short")}</span>
            <span class="bar-value">${value}</span>
          </button>`;
        })}
      </div>
    </section>`;
  }

  private _renderYearSummary(t: Translate, state: PanelState, stats: StatsResponse): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const summary = stats.year_summary;
    const scopes: [TextKey, Summary][] = [
      ["scope_total", summary.all],
      ["scope_internal", summary.internal],
      ["scope_external", summary.external],
    ];
    const rows: [TextKey, (scope: Summary) => string][] = [
      ["total_energy", (s) => formatEnergy(s.energy_kwh, locale, s.energy_is_estimate)],
      ["total_cost", (s) => formatCost(s.cost, locale, hass.config.currency)],
      ["total_duration", (s) => formatDuration(s.charge_duration_min)],
      ["total_sessions", (s) => String(s.count)],
    ];
    return html`<section class="year-summary">
      <h3>${t("year_summary_title", { year: state.year })}</h3>
      <table>
        <thead>
          <tr>
            <th></th>
            ${scopes.map(([label]) => html`<th class="num">${t(label)}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${rows.map(
            ([label, format]) => html`<tr>
              <th>${t(label)}</th>
              ${scopes.map(([, scope]) => html`<td class="num">${format(scope)}</td>`)}
            </tr>`,
          )}
        </tbody>
      </table>
    </section>`;
  }

  private _renderDetail(t: Translate, state: PanelState): TemplateResult {
    const sessions = this._sessions;
    const stats = this._stats;
    if (!sessions || !stats) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    const filters = state.filters;
    const visible = applyFilters(sessions, filters);
    const vehicles: Option[] = [
      ...vehicleOptions(this._vehicles, sessions),
      { value: UNASSIGNED, label: t("unassigned") },
    ];
    const cards: Option[] = [
      { value: NO_CARD, label: t("filter_no_card") },
      ...cardOptions(
        this._vehicles.flatMap((vehicle) => vehicle.cards),
        sessions,
        filters.card,
      ),
    ];
    return html`
      ${this._renderTiles(t, stats.months[state.month - 1])}
      <div class="filters">
        ${this._renderFilter(t("filter_vehicle"), "vehicle", vehicles, t)}
        ${this._renderFilter(
          t("filter_location"),
          "location",
          LOCATIONS.map((value) => ({ value, label: t(`location_${value}`) })),
          t,
        )}
        ${this._renderFilter(
          t("filter_charge_type"),
          "chargeType",
          CHARGE_TYPES.map((value) => ({ value, label: t(`charge_type_${value}`) })),
          t,
        )}
        ${this._renderFilter(t("filter_card"), "card", cards, t)}
        ${this._renderFilter(
          t("filter_status"),
          "status",
          STATUSES.map((value) => ({ value, label: t(`status_${value}`) })),
          t,
        )}
        ${hasActiveFilter(filters)
          ? html`<button
              class="text reset"
              @click=${() => this._setState({ filters: { ...EMPTY_FILTERS } })}
            >
              ${t("filter_reset")}
            </button>`
          : nothing}
      </div>
      <p class="count muted">
        ${t("filter_count", { shown: visible.length, total: sessions.length })}
      </p>
      ${visible.length === 0
        ? html`<div class="message">
            ${sessions.length === 0 ? t("no_sessions") : t("no_sessions_filtered")}
          </div>`
        : this._renderTable(visible, t, false)}
    `;
  }

  private _renderRecent(t: Translate): TemplateResult {
    const sessions = this._recent;
    if (!sessions) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    return sessions.length === 0
      ? html`<div class="message">${t("no_sessions")}</div>`
      : this._renderTable(sessions, t, true);
  }

  private _renderFilter(
    label: string,
    key: keyof Filters,
    options: Option[],
    t: Translate,
  ): TemplateResult {
    const value = this._state!.filters[key];
    return html`<label class="filter">
      <span class="muted">${label}</span>
      <select
        @change=${(event: Event) => this._setFilter(key, (event.target as HTMLSelectElement).value)}
      >
        <option value="" .selected=${value === ""}>${t("filter_all")}</option>
        ${options.map(
          (option) =>
            html`<option value=${option.value} .selected=${option.value === value}>
              ${option.label}
            </option>`,
        )}
      </select>
    </label>`;
  }

  private _renderTable(sessions: Session[], t: Translate, open: boolean): TemplateResult {
    return html`<div class="table" role="table">
      <div class="head" role="row">
        <span>${t("col_date")}</span>
        <span>${t("filter_vehicle")}</span>
        <span>${t("filter_location")}</span>
        <span>${t("filter_charge_type")}</span>
        <span class="num">${t("total_energy")}</span>
        <span class="num">${t("total_cost")}</span>
        <span class="num">${t("total_duration")}</span>
        <span>${t("filter_status")}</span>
      </div>
      ${sessions.map((session) => this._renderSession(session, t, open))}
    </div>`;
  }

  private _renderSession(session: Session, t: Translate, open: boolean): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const zone = hass.config.time_zone;
    const unassigned = session.vehicle_id === null;
    return html`<details class="session" ?open=${open}>
      <summary>
        <span class="c-date">${formatDateTime(session.plug_start, locale, zone)}</span>
        <span class=${classMap({ "c-vehicle": true, vehicle: true, unassigned })}
          >${vehicleLabel(session, t)}</span
        >
        <span class="c-location"><span class="chip">${t(`location_${session.location}`)}</span></span>
        <span class="c-type"><span class="chip">${t(`charge_type_${session.charge_type}`)}</span></span>
        <span class="c-energy num"
          >${formatEnergy(session.energy_kwh, locale, session.energy_is_estimate)}</span
        >
        <span class="c-cost num">${formatCost(session.cost, locale, hass.config.currency)}</span>
        <span class="c-duration num">${formatDuration(session.charge_duration_min)}</span>
        <span class="c-status">
          ${session.status === "complete"
            ? nothing
            : html`<span class="chip warn">${t(`status_${session.status}`)}</span>`}
          ${session.location_conflict
            ? html`<span class="chip alert">${t("flag_location_conflict")}</span>`
            : nothing}
          ${session.identification_conflict
            ? html`<span class="chip alert">${t("flag_identification_conflict")}</span>`
            : nothing}
          ${session.charge_error
            ? html`<span class="chip alert">${t("flag_charge_error")}</span>`
            : nothing}
          ${session.energy_unallocated_kwh > 0
            ? html`<span class="chip warn">${t("flag_unallocated_energy")}</span>`
            : nothing}
        </span>
      </summary>
      ${this._renderSessionBody(session, t)}
    </details>`;
  }

  private _row(
    label: string,
    value: string | TemplateResult | null,
  ): TemplateResult | typeof nothing {
    if (value === null || value === "" || value === EMPTY) {
      return nothing;
    }
    return html`<dt class="muted">${label}</dt>
      <dd>${value}</dd>`;
  }

  private _renderSessionBody(session: Session, t: Translate): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const zone = hass.config.time_zone;
    const isHome = session.location === "home";
    const notRecorded = t("detail_not_recorded");
    const soc =
      session.soc_start === null && session.soc_end === null
        ? null
        : `${formatPercent(session.soc_start, locale)} → ${formatPercent(session.soc_end, locale)}`;
    const location =
      session.address ??
      (session.latitude !== null && session.longitude !== null
        ? html`<a
            href=${`https://www.openstreetmap.org/?mlat=${session.latitude}&mlon=${session.longitude}#map=17/${session.latitude}/${session.longitude}`}
            target="_blank"
            rel="noopener noreferrer"
            >${t("detail_map_link")}</a
          >`
        : null);
    return html`<div class="body">
      <dl>
        ${this._row(t("detail_plug_start"), formatDateTime(session.plug_start, locale, zone))}
        ${this._row(t("detail_plug_end"), formatDateTime(session.plug_end, locale, zone))}
        ${this._row(t("detail_plug_duration"), formatDuration(session.plug_duration_min))}
        ${this._row(t("detail_charge_duration"), formatDuration(session.charge_duration_min))}
        ${session.pause_duration_min
          ? this._row(t("detail_pause_duration"), formatDuration(session.pause_duration_min))
          : nothing}
        ${this._row(t("detail_soc"), soc)}
        ${this._row(t("detail_odometer"), formatDistance(session.odometer_km, locale))}
        ${this._row(t("detail_power_avg"), formatPower(session.power_avg_kw, locale))}
        ${isHome
          ? html`${this._row(
              t("detail_energy_grid"),
              session.energy_grid_kwh === null
                ? notRecorded
                : formatEnergy(session.energy_grid_kwh, locale),
            )}
            ${this._row(
              t("detail_energy_solar"),
              session.energy_solar_kwh === null
                ? notRecorded
                : formatEnergy(session.energy_solar_kwh, locale),
            )}`
          : nothing}
        ${session.energy_unallocated_kwh > 0
          ? this._row(
              t("detail_energy_unallocated"),
              formatEnergy(session.energy_unallocated_kwh, locale),
            )
          : nothing}
        ${this._row(t("detail_card"), session.card_label ?? session.card_uid)}
        ${this._row(
          t("detail_identification"),
          t(`identification_${session.identification_source}`),
        )}
        ${this._row(t("detail_address"), location)}
        ${this._row(t("detail_provider"), session.provider)}
        ${this._row(t("detail_note"), session.note)}
        ${session.open_fields.length > 0
          ? this._row(
              t("detail_open_fields"),
              session.open_fields.map((name) => fieldLabel(name, t)).join(", "),
            )
          : nothing}
      </dl>
      ${this._renderPhases(session, t)}
    </div>`;
  }

  private _renderPhases(session: Session, t: Translate): TemplateResult {
    if (!session.phases_recorded || session.phases.length === 0) {
      return html`<p class="muted">${t("detail_phases_not_recorded")}</p>`;
    }
    const hass = this.hass!;
    const locale = hass.locale.language;
    const zone = hass.config.time_zone;
    return html`<table class="phases">
      <caption>
        ${t("detail_phases")}
      </caption>
      <thead>
        <tr>
          <th>${t("phase_start")}</th>
          <th>${t("phase_end")}</th>
          <th class="num">${t("phase_duration")}</th>
          <th class="num">${t("total_energy")}</th>
          <th class="num">${t("total_cost")}</th>
        </tr>
      </thead>
      <tbody>
        ${session.phases.map(
          (phase) => html`<tr>
            <td>${formatTime(phase.start, locale, zone)}</td>
            <td>${formatTime(phase.end, locale, zone)}</td>
            <td class="num">${formatDuration(phase.duration_min)}</td>
            <td class="num">${formatEnergy(phase.energy_kwh, locale)}</td>
            <td class="num">${formatCost(phase.cost, locale, hass.config.currency)}</td>
          </tr>`,
        )}
      </tbody>
    </table>`;
  }

  public static override styles = [
    sharedStyles,
    css`
      :host {
        display: block;
        --ev-columns: minmax(150px, 1.3fr) minmax(120px, 1.2fr) minmax(140px, 1.2fr) 56px
          minmax(110px, 0.9fr) minmax(90px, 0.7fr) minmax(80px, 0.6fr) minmax(110px, 1fr);
      }

      .view {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }

      .tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        border-bottom: 1px solid var(--ev-line);
      }

      .tab {
        padding: 10px 16px;
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        color: var(--ev-muted);
        cursor: pointer;
      }

      .tab.active {
        border-bottom-color: var(--ev-accent);
        color: var(--primary-text-color);
      }

      .period {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }

      button.icon {
        display: inline-flex;
        padding: 4px;
        background: transparent;
        border: none;
        border-radius: 50%;
        cursor: pointer;
      }

      .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px;
      }

      .tile {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px 14px;
        border: 1px solid var(--ev-line);
        border-radius: var(--ev-radius);
      }

      .tile-value {
        font-size: 1.4em;
        font-weight: 500;
      }

      .chart-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
      }

      .chart h3,
      .year-summary h3 {
        margin: 0;
        font-size: 1em;
        font-weight: 500;
      }

      .metric {
        display: inline-flex;
        align-items: center;
        gap: 8px;
      }

      .plot {
        display: flex;
        gap: 4px;
        margin-top: 12px;
      }

      .bar {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: stretch;
        min-width: 0;
        padding: 0;
        background: transparent;
        border: none;
        cursor: pointer;
      }

      .fill-area {
        height: 170px;
        display: flex;
        align-items: flex-end;
      }

      .fill {
        display: block;
        width: 100%;
        min-height: 2px;
        background: var(--ev-line);
        border-radius: 4px 4px 0 0;
      }

      .bar.selected .fill,
      .bar:hover .fill {
        background: var(--ev-accent);
      }

      .bar-label {
        padding-top: 4px;
        font-size: 0.75em;
      }

      .bar-value {
        padding-top: 2px;
        font-size: 0.75em;
        font-variant-numeric: tabular-nums;
        overflow-wrap: anywhere;
      }

      .bar.selected .bar-value {
        font-weight: 500;
      }

      .year-summary {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .year-summary table {
        width: 100%;
        border-collapse: collapse;
      }

      .year-summary th,
      .year-summary td {
        padding: 8px 12px;
        white-space: nowrap;
        border-bottom: 1px solid var(--ev-line);
        text-align: left;
        font-weight: 400;
      }

      .year-summary thead th {
        color: var(--ev-muted);
        font-size: 0.85em;
      }

      .year-summary tbody th {
        color: var(--ev-muted);
      }

      .year-summary .num {
        text-align: right;
      }

      .filters {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        align-items: end;
        gap: 12px;
      }

      .filter {
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-width: 0;
        font-size: 0.85em;
      }

      .filter select {
        width: 100%;
      }

      .count {
        margin: 0;
      }

      .table {
        border: 1px solid var(--ev-line);
        border-radius: var(--ev-radius);
        overflow: hidden;
      }

      .head,
      summary {
        display: grid;
        grid-template-columns: var(--ev-columns);
        column-gap: 16px;
        align-items: center;
        padding: 10px 44px 10px 14px;
      }

      .head {
        background: var(--ev-head-bg);
        border-bottom: 1px solid var(--ev-line);
        color: var(--ev-muted);
        font-size: 0.85em;
        font-weight: 500;
        text-transform: none;
      }

      .session + .session {
        border-top: 1px solid var(--ev-line);
      }

      summary {
        position: relative;
        cursor: pointer;
        list-style: none;
      }

      summary::-webkit-details-marker {
        display: none;
      }

      summary::after {
        content: "";
        position: absolute;
        top: 50%;
        right: 18px;
        width: 7px;
        height: 7px;
        margin-top: -6px;
        border-right: 2px solid var(--ev-muted);
        border-bottom: 2px solid var(--ev-muted);
        transform: rotate(45deg);
      }

      details[open] > summary::after {
        margin-top: -2px;
        transform: rotate(-135deg);
      }

      .c-status {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      .head span:last-child,
      .c-status {
        padding-left: 8px;
      }

      .c-location .chip {
        white-space: normal;
      }

      .c-type .chip {
        background: color-mix(in srgb, var(--primary-text-color) 12%, transparent);
      }

      .body {
        padding: 4px 14px 14px;
        background: var(--ev-head-bg);
        border-top: 1px solid var(--ev-line);
      }

      dl {
        display: grid;
        grid-template-columns: minmax(120px, max-content) 1fr;
        gap: 4px 16px;
        margin: 8px 0 0;
      }

      dd {
        margin: 0;
        overflow-wrap: anywhere;
      }

      .phases {
        width: 100%;
        margin-top: 12px;
        border-collapse: collapse;
        font-size: 0.9em;
      }

      .phases caption {
        padding-bottom: 4px;
        color: var(--ev-muted);
        text-align: left;
      }

      .phases th,
      .phases td {
        padding: 4px 8px 4px 0;
        text-align: left;
      }

      .phases .num {
        text-align: right;
      }

      .hint {
        margin: 0;
        font-size: 0.85em;
      }

      @media (max-width: 800px) {
        .head {
          display: none;
        }

        summary {
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px 12px;
        }

        .c-date {
          grid-column: 1 / 3;
          font-weight: 500;
        }

        .c-vehicle {
          text-align: right;
        }

        .c-energy,
        .c-cost,
        .c-duration {
          order: 1;
        }

        .c-location,
        .c-type,
        .c-status {
          order: 2;
        }

        .c-energy {
          text-align: left;
        }

        .c-duration {
          text-align: right;
        }

        .c-cost {
          text-align: center;
        }

        .c-type {
          text-align: center;
        }

        .c-status {
          justify-content: flex-end;
          padding-left: 0;
        }

        .year-summary th,
        .year-summary td {
          padding: 8px 6px;
          font-size: 0.9em;
        }

        .bar-value {
          writing-mode: vertical-rl;
          transform: rotate(180deg);
          align-self: center;
          padding-top: 6px;
        }
      }
    `,
  ];
}
