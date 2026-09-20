import { css, html, nothing, type TemplateResult } from "lit";
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
} from "./format";
import type { Translate } from "./i18n";
import { fieldLabel } from "./labels";
import { mapUrl, phasesNotice } from "./logic";
import type { HomeAssistant, Session } from "./types";

const MAP_MARKER =
  "M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z";

function row(label: string, value: string | TemplateResult | null): TemplateResult | typeof nothing {
  if (value === null || value === "" || value === EMPTY) {
    return nothing;
  }
  return html`<dt class="muted">${label}</dt>
    <dd>${value}</dd>`;
}

function renderLocation(session: Session, t: Translate): TemplateResult | null {
  const url = mapUrl(session);
  if (session.address === null && url === null) {
    return null;
  }
  return html`${session.address ?? nothing}${url === null
    ? nothing
    : html`<a
        class="map"
        href=${url}
        target="_blank"
        rel="noopener noreferrer"
        title=${t("detail_map_link")}
        aria-label=${t("detail_map_link")}
        ><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path d=${MAP_MARKER} fill="currentColor"></path></svg
        >${session.address === null ? t("detail_map_link") : nothing}</a
      >`}`;
}

function renderPhases(session: Session, t: Translate, hass: HomeAssistant): TemplateResult {
  const notice = phasesNotice(session);
  if (notice !== null) {
    return html`<p class="muted">${t(notice)}</p>`;
  }
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

// The expanded details of one session, shared by the table, the list of the
// latest sessions and the card.
export function renderSessionBody(
  session: Session,
  t: Translate,
  hass: HomeAssistant,
): TemplateResult {
  const locale = hass.locale.language;
  const zone = hass.config.time_zone;
  const notRecorded = t("detail_not_recorded");
  const soc =
    session.soc_start === null && session.soc_end === null
      ? null
      : `${formatPercent(session.soc_start, locale)} → ${formatPercent(session.soc_end, locale)}`;
  return html`<div class="body">
    <dl>
      ${row(t("detail_plug_start"), formatDateTime(session.plug_start, locale, zone))}
      ${row(t("detail_plug_end"), formatDateTime(session.plug_end, locale, zone))}
      ${row(t("detail_plug_duration"), formatDuration(session.plug_duration_min))}
      ${row(t("detail_charge_duration"), formatDuration(session.charge_duration_min))}
      ${session.pause_duration_min
        ? row(t("detail_pause_duration"), formatDuration(session.pause_duration_min))
        : nothing}
      ${row(t("detail_soc"), soc)}
      ${row(t("detail_odometer"), formatDistance(session.odometer_km, locale))}
      ${row(t("detail_power_avg"), formatPower(session.power_avg_kw, locale))}
      ${session.location === "home"
        ? html`${row(
            t("detail_energy_grid"),
            session.energy_grid_kwh === null
              ? notRecorded
              : formatEnergy(session.energy_grid_kwh, locale),
          )}
          ${row(
            t("detail_energy_solar"),
            session.energy_solar_kwh === null
              ? notRecorded
              : formatEnergy(session.energy_solar_kwh, locale),
          )}`
        : nothing}
      ${session.energy_unallocated_kwh > 0
        ? row(t("detail_energy_unallocated"), formatEnergy(session.energy_unallocated_kwh, locale))
        : nothing}
      ${row(t("detail_card"), session.card_label ?? session.card_uid)}
      ${row(t("detail_identification"), t(`identification_${session.identification_source}`))}
      ${row(t("detail_address"), renderLocation(session, t))}
      ${row(t("detail_provider"), session.provider)}
      ${row(t("detail_note"), session.note)}
      ${session.open_fields.length > 0
        ? row(
            t("detail_open_fields"),
            session.open_fields.map((name) => fieldLabel(name, t)).join(", "),
          )
        : nothing}
    </dl>
    ${renderPhases(session, t, hass)}
  </div>`;
}

export const sessionBodyStyles = css`
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

  .map {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-left: 6px;
    vertical-align: middle;
    color: var(--ev-accent);
    text-decoration: none;
  }

  .map:hover {
    text-decoration: underline;
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
    font-variant-numeric: tabular-nums;
  }
`;
