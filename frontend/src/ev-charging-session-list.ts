import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { formatCost, formatDateTime, formatDuration, formatEnergy, formatPercent } from "./format";
import type { Translate } from "./i18n";
import { vehicleLabel } from "./labels";
import { renderSessionBody, sessionBodyStyles } from "./session-body";
import { sharedStyles } from "./styles";
import type { HomeAssistant, Session } from "./types";

// A compact list of sessions: vehicle on top, date and state of charge muted,
// details behind an expander. Used by the list of the latest sessions in the
// panel and by ev-charging-recent-card.
export class EvChargingSessionList extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property({ attribute: false }) public t?: Translate;
  @property({ attribute: false }) public sessions: Session[] = [];

  protected override render(): TemplateResult | typeof nothing {
    const t = this.t;
    if (!t || !this.hass) {
      return nothing;
    }
    return html`<ul>
      ${this.sessions.map((session) => this._renderSession(session, t))}
    </ul>`;
  }

  private _renderSession(session: Session, t: Translate): TemplateResult {
    const hass = this.hass!;
    const locale = hass.locale.language;
    const soc =
      session.soc_start !== null && session.soc_end !== null
        ? `${formatPercent(session.soc_start, locale)} → ${formatPercent(session.soc_end, locale)}`
        : nothing;
    return html`<li>
      <details>
        <summary>
          <div class="line">
            <span class=${classMap({ vehicle: true, unassigned: session.vehicle_id === null })}
              >${vehicleLabel(session, t)}</span
            >
            <span class="muted"
              >${formatDateTime(session.plug_start, locale, hass.config.time_zone)}</span
            >
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
            <span class="chips">
              <span class="chip">${t(`location_${session.location}`)}</span>
              ${session.status === "complete"
                ? nothing
                : html`<span class="chip warn">${t(`status_${session.status}`)}</span>`}
            </span>
          </div>
        </summary>
        ${renderSessionBody(session, t, hass)}
      </details>
    </li>`;
  }

  public static override styles = [
    sharedStyles,
    sessionBodyStyles,
    css`
      :host {
        display: block;
      }

      ul {
        display: flex;
        flex-direction: column;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      li + li {
        border-top: 1px solid var(--ev-line);
      }

      summary {
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 10px 28px 10px 0;
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
        right: 6px;
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

      .line {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 4px 12px;
      }

      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      .vehicle {
        font-weight: 500;
      }

      .body {
        margin-bottom: 10px;
        border-radius: var(--ev-radius);
      }
    `,
  ];
}
