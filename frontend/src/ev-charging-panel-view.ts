import { LitElement, css, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import {
  closeFollowup,
  correctVehicle,
  createSession,
  deleteSession,
  listOpenSessions,
  listSessions,
  listVehicles,
  listYear,
  updateSession,
  type SessionCreate,
} from "./api";
import { onConnectionReady } from "./connection";
import "./ev-charging-session-list";
import {
  EMPTY,
  formatCost,
  formatCostWhole,
  formatDateTime,
  formatDuration,
  formatDurationWhole,
  formatEnergy,
  formatEnergyWhole,
  monthName,
} from "./format";
import { loadTranslate, makeTranslate, type TextKey, type Translate } from "./i18n";
import { vehicleLabel } from "./labels";
import {
  EMPTY_FILTERS,
  NO_CARD,
  UNASSIGNED,
  applyFilters,
  cardOptions,
  currentYearMonth,
  defaultState,
  hasActiveFilter,
  monthlySummaries,
  sessionsOfMonth,
  shiftMonth,
  summarizeSessions,
  summarizeYear,
  vehicleOptions,
  yearOptions,
  type Filters,
  type Option,
  type PanelState,
  type ViewId,
} from "./logic";
import { renderSessionBody, sessionBodyStyles } from "./session-body";
import {
  buildUpdatePayload,
  editStyles,
  fieldsForCorrection,
  fieldsForOpenSession,
  hasUpdatePayload,
  renderEditFields,
  renderVehicleSelect,
  type EditFieldName,
  type EditValues,
} from "./session-edit";
import { sharedStyles } from "./styles";
import type {
  ChargeType,
  HomeAssistant,
  MonthStats,
  Session,
  SessionLocation,
  SessionStatus,
  Summary,
  Vehicle,
  YearSummary,
} from "./types";

const REFRESH_INTERVAL_MS = 10 * 60 * 1000;
const RECENT_COUNT = 5;

// Pseudo id under which the create-session form tracks its own busy and
// error state, alongside the per-session ids used by the other actions.
const CREATE_KEY = "__create__";

const CHEVRON_LEFT = "M15.41,16.58L10.83,12L15.41,7.42L14,6L8,12L14,18L15.41,16.58Z";
const CHEVRON_RIGHT = "M8.59,16.58L13.17,12L8.59,7.42L10,6L16,12L10,18L8.59,16.58Z";

const VIEWS: { id: ViewId; label: TextKey }[] = [
  { id: "overview", label: "view_overview" },
  { id: "recent", label: "view_recent" },
  { id: "detail", label: "view_detail" },
  { id: "followup", label: "view_followup" },
  { id: "correction", label: "view_correction" },
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
  @state() private _yearSessions?: Session[];
  @state() private _years: number[] = [];
  @state() private _recent?: Session[];
  @state() private _vehicles: Vehicle[] = [];
  @state() private _failed = false;
  @state() private _metric: Metric = "energy";

  @state() private _openSessions?: Session[];
  @state() private _editingId: string | null = null;
  @state() private _editValues: Record<string, EditValues> = {};
  @state() private _vehicleDraft: Record<string, string> = {};
  @state() private _busyId: string | null = null;
  @state() private _editError: Record<string, string> = {};
  @state() private _creating = false;
  @state() private _createValues: Record<string, string> = {};

  private _started = false;
  private _yearKey?: number;
  private _recentRequested = false;
  private _openRequested = false;
  private _timer?: number;
  private _connectionUnsub?: () => void;

  public override connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => this._refresh(), REFRESH_INTERVAL_MS);
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
    this._watchConnection(hass);
    if (!this._started) {
      this._started = true;
      void this._loadShared(hass, false);
    }
    if (
      state.view !== "recent" &&
      state.view !== "followup" &&
      this._yearKey !== state.year
    ) {
      this._yearKey = state.year;
      this._yearSessions = undefined;
      void this._loadYear(hass, state.year, false);
    }
    if (state.view === "recent" && !this._recentRequested) {
      this._recentRequested = true;
      void this._loadRecent(hass, false);
    }
    if (state.view === "followup" && !this._openRequested) {
      this._openRequested = true;
      void this._loadOpenSessions(hass, false);
    }
  }

  private _refresh(): void {
    const hass = this.hass;
    const state = this._state;
    if (!hass || !state || !this._started || this._failed) {
      return;
    }
    void this._loadShared(hass, true);
    if (state.view !== "recent" && state.view !== "followup") {
      void this._loadYear(hass, state.year, true);
    }
    if (state.view === "recent") {
      void this._loadRecent(hass, true);
    }
    if (state.view === "followup") {
      void this._loadOpenSessions(hass, true);
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
    this._yearKey = undefined;
    this._recentRequested = false;
    this._openRequested = false;
    this.requestUpdate();
  }

  // A load that raced a reconnect leaves the view failed; retry once the
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

  private async _loadYear(hass: HomeAssistant, year: number, silent: boolean): Promise<void> {
    try {
      const result = await listYear(hass, year);
      if (this._yearKey === year) {
        this._yearSessions = result.sessions;
        this._years = result.years;
      }
    } catch (error) {
      if (this._yearKey === year) {
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

  private async _loadOpenSessions(hass: HomeAssistant, silent: boolean): Promise<void> {
    try {
      this._openSessions = await listOpenSessions(hass);
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
    const withPeriod = state.view === "overview" || state.view === "detail" || state.view === "correction";
    return html`
      <div class="view">
        ${this._renderTabs(t, state)}
        ${withPeriod ? this._renderFilters(t, state) : nothing}
        ${withPeriod ? this._renderPeriod(t, state) : nothing}
        ${state.view === "overview"
          ? this._renderOverview(t, state)
          : state.view === "detail"
            ? this._renderDetail(t, state)
            : state.view === "followup"
              ? this._renderFollowup(t)
              : state.view === "correction"
                ? this._renderCorrection(t, state)
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
    const years = yearOptions(this._years, current.year, state.year);
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

  private _renderTiles(t: Translate, month: Summary): TemplateResult {
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

  // Sessions of the selected year that pass the filters.
  private _filteredYear(state: PanelState): Session[] {
    return applyFilters(this._yearSessions ?? [], state.filters);
  }

  private _renderOverview(t: Translate, state: PanelState): TemplateResult {
    if (!this._yearSessions) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    const filtered = this._filteredYear(state);
    const zone = this.hass!.config.time_zone;
    const months = monthlySummaries(filtered, zone);
    return html`
      ${this._renderTiles(t, months[state.month - 1])}
      ${this._renderChart(t, state, months)}
      ${this._renderYearSummary(t, state, summarizeYear(filtered))}
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
        return formatCostWhole(month.cost, locale, hass.config.currency);
      case "duration":
        return formatDurationWhole(month.charge_duration_min);
      default:
        return formatEnergyWhole(month.energy_kwh, locale, month.energy_is_estimate);
    }
  }

  private _renderChart(t: Translate, state: PanelState, months: MonthStats[]): TemplateResult {
    const locale = this.hass!.locale.language;
    const maximum = Math.max(...months.map((month) => this._metricValue(month)), 0);
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
        ${months.map((month) => {
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

  private _renderYearSummary(t: Translate, state: PanelState, summary: YearSummary): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const scopes: [TextKey, Summary][] = [
      ["scope_total", summary.all],
      ["scope_internal", summary.internal],
      ["scope_external", summary.external],
    ];
    const rows: [TextKey, (scope: Summary) => string][] = [
      ["total_energy", (s) => formatEnergyWhole(s.energy_kwh, locale, s.energy_is_estimate)],
      ["total_cost", (s) => formatCostWhole(s.cost, locale, hass.config.currency)],
      ["total_duration", (s) => formatDurationWhole(s.charge_duration_min)],
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

  private _renderFilters(t: Translate, state: PanelState): TemplateResult {
    const sessions = this._yearSessions ?? [];
    const filters = state.filters;
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
    return html`<div class="filters">
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
    </div>`;
  }

  private _renderDetail(t: Translate, state: PanelState): TemplateResult {
    if (!this._yearSessions) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    const zone = this.hass!.config.time_zone;
    const ofMonth = sessionsOfMonth(this._yearSessions, state.month, zone);
    const visible = applyFilters(ofMonth, state.filters);
    return html`
      ${this._renderTiles(t, summarizeSessions(visible))}
      <p class="count muted">
        ${t("filter_count", { shown: visible.length, total: ofMonth.length })}
      </p>
      ${visible.length === 0
        ? html`<div class="message">
            ${ofMonth.length === 0 ? t("no_sessions") : t("no_sessions_filtered")}
          </div>`
        : this._renderTable(visible, t)}
    `;
  }

  private _renderRecent(t: Translate): TemplateResult {
    const sessions = this._recent;
    if (!sessions) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    return sessions.length === 0
      ? html`<div class="message">${t("no_sessions")}</div>`
      : html`<ev-charging-session-list
          .hass=${this.hass}
          .t=${t}
          .sessions=${sessions}
        ></ev-charging-session-list>`;
  }

  // ----------------------------------------------------------- nacherfassung

  private _setDraft(id: string, field: EditFieldName, value: string): void {
    this._editValues = { ...this._editValues, [id]: { ...this._editValues[id], [field]: value } };
  }

  private _setVehicleDraft(id: string, value: string): void {
    this._vehicleDraft = { ...this._vehicleDraft, [id]: value };
  }

  private static _omit<T>(record: Record<string, T>, id: string): Record<string, T> {
    const next = { ...record };
    delete next[id];
    return next;
  }

  private async _run(
    id: string,
    action: () => Promise<unknown>,
    reload: () => Promise<void>,
  ): Promise<void> {
    this._busyId = id;
    try {
      await action();
      this._editValues = EvChargingPanelView._omit(this._editValues, id);
      this._editError = EvChargingPanelView._omit(this._editError, id);
      await reload();
    } catch (error) {
      console.error("ev_charging: session correction failed", error);
      this._editError = { ...this._editError, [id]: this._t?.("edit_error") ?? "error" };
    } finally {
      this._busyId = null;
    }
  }

  private async _saveUpdate(session: Session, reload: () => Promise<void>): Promise<void> {
    const payload = buildUpdatePayload(this._editValues[session.id] ?? {});
    if (Object.keys(payload).length === 0) {
      return;
    }
    await this._run(session.id, () => updateSession(this.hass!, session.id, payload), reload);
  }

  private async _saveVehicle(session: Session, reload: () => Promise<void>): Promise<void> {
    const vehicleId = this._vehicleDraft[session.id];
    if (!vehicleId) {
      return;
    }
    await this._run(session.id, () => correctVehicle(this.hass!, session.id, vehicleId), reload);
  }

  private async _accept(session: Session, reload: () => Promise<void>): Promise<void> {
    await this._run(session.id, () => closeFollowup(this.hass!, session.id), reload);
  }

  private async _remove(session: Session, reload: () => Promise<void>): Promise<void> {
    if (!window.confirm(this._t?.("edit_delete_confirm") ?? "")) {
      return;
    }
    this._editingId = null;
    await this._run(
      session.id,
      async () => {
        await deleteSession(this.hass!, session.id);
      },
      reload,
    );
  }

  private _renderFollowup(t: Translate): TemplateResult {
    const sessions = this._openSessions;
    if (!sessions) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    if (sessions.length === 0) {
      return html`<div class="message">${t("followup_empty")}</div>`;
    }
    const reload = () => this._loadOpenSessions(this.hass!, true);
    return html`<div class="followup-list">
      ${sessions.map((session) => this._renderFollowupRow(session, t, reload))}
    </div>`;
  }

  private _renderFollowupRow(
    session: Session,
    t: Translate,
    reload: () => Promise<void>,
  ): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const zone = hass.config.time_zone;
    const fields = fieldsForOpenSession(session);
    const values = this._editValues[session.id] ?? {};
    const busy = this._busyId === session.id;
    const error = this._editError[session.id];
    return html`<div class="followup-row">
      <div class="followup-head">
        <span class=${classMap({ vehicle: true, unassigned: session.vehicle_id === null })}
          >${vehicleLabel(session, t)}</span
        >
        <span class="muted">${formatDateTime(session.plug_start, locale, zone)}</span>
        <span class="chip">${t(`location_${session.location}`)}</span>
      </div>
      ${session.open_fields.includes("vehicle_id")
        ? html`<div class="edit-vehicle">
            ${renderVehicleSelect(
              this._vehicles,
              this._vehicleDraft[session.id] ?? "",
              (value) => this._setVehicleDraft(session.id, value),
              t,
            )}
            <button
              class="text"
              ?disabled=${busy || !this._vehicleDraft[session.id]}
              @click=${() => this._saveVehicle(session, reload)}
            >
              ${t("edit_assign_vehicle")}
            </button>
          </div>`
        : nothing}
      ${fields.length > 0
        ? renderEditFields(
            session,
            fields,
            values,
            (field, value) => this._setDraft(session.id, field, value),
            t,
          )
        : nothing}
      <div class="edit-actions">
        ${fields.length > 0
          ? html`<button
              class="text"
              ?disabled=${busy || !hasUpdatePayload(values)}
              @click=${() => this._saveUpdate(session, reload)}
            >
              ${t("edit_save")}
            </button>`
          : nothing}
        <button class="text" ?disabled=${busy} @click=${() => this._accept(session, reload)}>
          ${t("edit_accept")}
        </button>
        ${error ? html`<span class="edit-message error">${error}</span>` : nothing}
      </div>
    </div>`;
  }

  // -------------------------------------------------------------- korrektur

  private _toggleEdit(id: string): void {
    this._editingId = this._editingId === id ? null : id;
  }

  private _toggleCreate(): void {
    this._creating = !this._creating;
    if (!this._creating) {
      this._createValues = {};
    }
  }

  private async _createNew(reload: () => Promise<void>): Promise<void> {
    const values = this._createValues;
    if (!values.location || !values.plug_start || !values.plug_end) {
      return;
    }
    const fields: SessionCreate = {
      location: values.location as SessionLocation,
      plug_start: new Date(values.plug_start).toISOString(),
      plug_end: new Date(values.plug_end).toISOString(),
    };
    if (values.vehicle_id) fields.vehicle_id = values.vehicle_id;
    if (values.soc_start) fields.soc_start = Number(values.soc_start);
    if (values.soc_end) fields.soc_end = Number(values.soc_end);
    if (values.odometer_km) fields.odometer_km = Number(values.odometer_km);
    if (values.energy_billed_kwh) fields.energy_billed_kwh = Number(values.energy_billed_kwh);
    if (values.charge_type) fields.charge_type = values.charge_type as ChargeType;
    if (values.cost) fields.cost = Number(values.cost);
    if (values.address) fields.address = values.address;
    if (values.note) fields.note = values.note;
    if (values.provider) fields.provider = values.provider;
    await this._run(CREATE_KEY, () => createSession(this.hass!, fields), reload);
    this._creating = false;
    this._createValues = {};
  }

  private _renderCorrection(t: Translate, state: PanelState): TemplateResult {
    if (!this._yearSessions) {
      return html`<div class="spinner" role="progressbar"></div>`;
    }
    const zone = this.hass!.config.time_zone;
    const ofMonth = sessionsOfMonth(this._yearSessions, state.month, zone);
    const visible = applyFilters(ofMonth, state.filters);
    const reload = () => this._loadYear(this.hass!, state.year, true);
    return html`
      <div class="edit-actions">
        <button class="text" @click=${() => this._toggleCreate()}>
          ${t("edit_new_session")}
        </button>
      </div>
      ${this._creating ? this._renderCreateForm(t, reload) : nothing}
      <p class="count muted">
        ${t("filter_count", { shown: visible.length, total: ofMonth.length })}
      </p>
      ${visible.length === 0
        ? html`<div class="message">
            ${ofMonth.length === 0 ? t("no_sessions") : t("no_sessions_filtered")}
          </div>`
        : this._renderCorrectionTable(visible, t, reload)}
    `;
  }

  private _renderCorrectionTable(
    sessions: Session[],
    t: Translate,
    reload: () => Promise<void>,
  ): TemplateResult {
    return html`<div class="correction-table">
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
      ${sessions.map((session) => this._renderCorrectionRow(session, t, reload))}
    </div>`;
  }

  private _renderCorrectionRow(
    session: Session,
    t: Translate,
    reload: () => Promise<void>,
  ): TemplateResult {
    const editing = this._editingId === session.id;
    const error = this._editError[session.id];
    return html`<div class="correction-item">
      ${this._renderSession(session, t)}
      <div class="edit-actions">
        <button class="text" @click=${() => this._toggleEdit(session.id)}>
          ${t(editing ? "edit_cancel" : "edit_edit")}
        </button>
        <button
          class="text danger"
          ?disabled=${this._busyId === session.id}
          @click=${() => this._remove(session, reload)}
        >
          ${t("edit_delete")}
        </button>
        ${error ? html`<span class="edit-message error">${error}</span>` : nothing}
      </div>
      ${editing ? this._renderCorrectionForm(session, t, reload) : nothing}
    </div>`;
  }

  private _renderCorrectionForm(
    session: Session,
    t: Translate,
    reload: () => Promise<void>,
  ): TemplateResult {
    const values = this._editValues[session.id] ?? {};
    const busy = this._busyId === session.id;
    const fields = fieldsForCorrection(session);
    const vehicleDraft = this._vehicleDraft[session.id] ?? session.vehicle_id ?? "";
    return html`<div class="edit-form">
      <div class="edit-vehicle">
        ${renderVehicleSelect(
          this._vehicles,
          vehicleDraft,
          (value) => this._setVehicleDraft(session.id, value),
          t,
        )}
        <button
          class="text"
          ?disabled=${busy || !vehicleDraft || vehicleDraft === session.vehicle_id}
          @click=${() => this._saveVehicle(session, reload)}
        >
          ${t("edit_assign_vehicle")}
        </button>
      </div>
      ${renderEditFields(
        session,
        fields,
        values,
        (field, value) => this._setDraft(session.id, field, value),
        t,
      )}
      <div class="edit-actions">
        <button
          class="text"
          ?disabled=${busy || !hasUpdatePayload(values)}
          @click=${() => this._saveUpdate(session, reload)}
        >
          ${t("edit_save")}
        </button>
        ${session.status === "followup_open" || session.open_fields.length > 0
          ? html`<button class="text" ?disabled=${busy} @click=${() => this._accept(session, reload)}>
              ${t("edit_accept")}
            </button>`
          : nothing}
      </div>
    </div>`;
  }

  private _renderCreateForm(t: Translate, reload: () => Promise<void>): TemplateResult {
    const values = this._createValues;
    const set = (field: string, value: string): void => {
      this._createValues = { ...this._createValues, [field]: value };
    };
    const busy = this._busyId === CREATE_KEY;
    const error = this._editError[CREATE_KEY];
    const ready = Boolean(values.location && values.plug_start && values.plug_end);
    return html`<div class="edit-form">
      <div class="edit-fields">
        <label class="edit-row">
          <span class="muted">${t("filter_location")}</span>
          <select @change=${(event: Event) => set("location", (event.target as HTMLSelectElement).value)}>
            <option value="" .selected=${!values.location}>${t("filter_all")}</option>
            ${LOCATIONS.map(
              (location) =>
                html`<option value=${location} .selected=${values.location === location}>
                  ${t(`location_${location}`)}
                </option>`,
            )}
          </select>
        </label>
        <label class="edit-row">
          <span class="muted">${t("detail_plug_start")}</span>
          <input
            type="datetime-local"
            .value=${values.plug_start ?? ""}
            @input=${(event: Event) => set("plug_start", (event.target as HTMLInputElement).value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${t("detail_plug_end")}</span>
          <input
            type="datetime-local"
            .value=${values.plug_end ?? ""}
            @input=${(event: Event) => set("plug_end", (event.target as HTMLInputElement).value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${t("filter_vehicle")}</span>
          ${renderVehicleSelect(
            this._vehicles,
            values.vehicle_id ?? "",
            (value) => set("vehicle_id", value),
            t,
          )}
        </label>
        <label class="edit-row">
          <span class="muted">${t("field_soc_start")}</span>
          <input
            type="number"
            min="0"
            max="100"
            step="0.1"
            .value=${values.soc_start ?? ""}
            @input=${(event: Event) => set("soc_start", (event.target as HTMLInputElement).value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${t("field_soc_end")}</span>
          <input
            type="number"
            min="0"
            max="100"
            step="0.1"
            .value=${values.soc_end ?? ""}
            @input=${(event: Event) => set("soc_end", (event.target as HTMLInputElement).value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${t("field_odometer_km")}</span>
          <input
            type="number"
            min="0"
            step="0.1"
            .value=${values.odometer_km ?? ""}
            @input=${(event: Event) => set("odometer_km", (event.target as HTMLInputElement).value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${t("field_energy_billed_kwh")}</span>
          <input
            type="number"
            min="0"
            step="0.001"
            .value=${values.energy_billed_kwh ?? ""}
            @input=${(event: Event) =>
              set("energy_billed_kwh", (event.target as HTMLInputElement).value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${t("filter_charge_type")}</span>
          <select
            @change=${(event: Event) => set("charge_type", (event.target as HTMLSelectElement).value)}
          >
            <option value="" .selected=${!values.charge_type}>${t("filter_all")}</option>
            <option value="ac" .selected=${values.charge_type === "ac"}>${t("charge_type_ac")}</option>
            <option value="dc" .selected=${values.charge_type === "dc"}>${t("charge_type_dc")}</option>
          </select>
        </label>
        <label class="edit-row">
          <span class="muted">${t("field_cost")}</span>
          <input
            type="number"
            min="0"
            step="0.01"
            .value=${values.cost ?? ""}
            @input=${(event: Event) => set("cost", (event.target as HTMLInputElement).value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${t("detail_address")}</span>
          <input
            type="text"
            .value=${values.address ?? ""}
            @input=${(event: Event) => set("address", (event.target as HTMLInputElement).value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${t("detail_provider")}</span>
          <input
            type="text"
            .value=${values.provider ?? ""}
            @input=${(event: Event) => set("provider", (event.target as HTMLInputElement).value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${t("detail_note")}</span>
          <input
            type="text"
            .value=${values.note ?? ""}
            @input=${(event: Event) => set("note", (event.target as HTMLInputElement).value)}
          />
        </label>
      </div>
      <div class="edit-actions">
        <button class="text" ?disabled=${busy || !ready} @click=${() => this._createNew(reload)}>
          ${t("edit_create")}
        </button>
        ${error ? html`<span class="edit-message error">${error}</span>` : nothing}
      </div>
    </div>`;
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

  private _renderTable(sessions: Session[], t: Translate): TemplateResult {
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
      ${sessions.map((session) => this._renderSession(session, t))}
    </div>`;
  }

  private _renderSession(session: Session, t: Translate): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const zone = hass.config.time_zone;
    const unassigned = session.vehicle_id === null;
    return html`<details class="session">
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
      ${renderSessionBody(session, t, hass)}
    </details>`;
  }

  public static override styles = [
    sharedStyles,
    sessionBodyStyles,
    editStyles,
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
        gap: 0;
        margin-top: 24px;
      }

      .year-summary h3 {
        margin-bottom: 2px;
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
        padding-top: 2px;
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

      .hint {
        margin: 0;
        font-size: 0.85em;
      }

      .followup-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .followup-row {
        padding: 12px 14px;
        border: 1px solid var(--ev-line);
        border-radius: var(--ev-radius);
      }

      .followup-head {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px 12px;
      }

      .followup-head .vehicle {
        font-weight: 500;
      }

      .correction-table .head {
        margin-bottom: 12px;
        border-radius: var(--ev-radius) var(--ev-radius) 0 0;
      }

      .correction-item {
        margin-bottom: 12px;
        border: 1px solid var(--ev-line);
        border-radius: var(--ev-radius);
        overflow: hidden;
      }

      .correction-item .edit-actions,
      .correction-item .edit-form {
        margin: 0;
        padding: 10px 14px;
      }

      .correction-item .edit-form {
        border: none;
        border-top: 1px solid var(--ev-line);
        border-radius: 0;
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
