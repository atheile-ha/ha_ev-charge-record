import { css, html, nothing, type TemplateResult } from "lit";
import type { SessionUpdate } from "./api";
import type { Translate } from "./i18n";
import type { ChargeType, Session, Vehicle } from "./types";

// The fields update_session may change (10, 13, 15). vehicle_id is not among
// them: it runs exclusively through correct_vehicle (7.8), rendered
// separately by renderVehicleSelect.
export type EditFieldName =
  | "soc_start"
  | "soc_end"
  | "odometer_km"
  | "energy_billed_kwh"
  | "cost"
  | "charge_type"
  | "address"
  | "note"
  | "provider"
  | "plug_end";

// Raw, as-typed input values, keyed by field. A field the user never
// touched is absent, so it contributes nothing to the update payload.
export type EditValues = Partial<Record<EditFieldName, string>>;

const CORRECTION_FIELDS: EditFieldName[] = [
  "soc_start",
  "soc_end",
  "odometer_km",
  "energy_billed_kwh",
  "cost",
  "charge_type",
  "address",
  "note",
  "provider",
  "plug_end",
];

// Which edit fields can fill a given open_fields entry. energy_kwh has no
// field of its own: it is derived from energy_billed_kwh or from soc_start
// and soc_end together (8.4).
const OPEN_FIELD_TO_EDIT_FIELDS: Partial<Record<string, EditFieldName[]>> = {
  soc_start: ["soc_start"],
  soc_end: ["soc_end"],
  odometer_km: ["odometer_km"],
  cost: ["cost"],
  energy_kwh: ["soc_start", "soc_end", "energy_billed_kwh"],
};

// The fields a follow-up task list should offer for one session: exactly
// those that can fill one of its open_fields.
export function fieldsForOpenSession(session: Session): EditFieldName[] {
  const fields = new Set<EditFieldName>();
  for (const open of session.open_fields) {
    for (const field of OPEN_FIELD_TO_EDIT_FIELDS[open] ?? []) {
      fields.add(field);
    }
  }
  return CORRECTION_FIELDS.filter((field) => fields.has(field));
}

// Every field a general correction may touch, minus the ones that do not
// apply to this session (charge_type outside a heuristic determination,
// plug_end once it is already set).
export function fieldsForCorrection(session: Session): EditFieldName[] {
  return CORRECTION_FIELDS.filter((field) => {
    if (field === "charge_type") return session.charge_type_source === "heuristic";
    if (field === "plug_end") return session.plug_end === null;
    return true;
  });
}

function row(label: string, control: TemplateResult): TemplateResult {
  return html`<label class="edit-row"><span class="muted">${label}</span>${control}</label>`;
}

function numberInput(
  field: EditFieldName,
  value: string,
  onChange: (field: EditFieldName, value: string) => void,
  min: number,
  max: number | undefined,
  step: string,
): TemplateResult {
  return html`<input
    type="number"
    min=${min}
    max=${max ?? nothing}
    step=${step}
    .value=${value}
    @input=${(event: Event) => onChange(field, (event.target as HTMLInputElement).value)}
  />`;
}

function textInput(
  field: EditFieldName,
  value: string,
  onChange: (field: EditFieldName, value: string) => void,
): TemplateResult {
  return html`<input
    type="text"
    .value=${value}
    @input=${(event: Event) => onChange(field, (event.target as HTMLInputElement).value)}
  />`;
}

function renderField(
  session: Session,
  field: EditFieldName,
  values: EditValues,
  onChange: (field: EditFieldName, value: string) => void,
  t: Translate,
): TemplateResult | typeof nothing {
  const value = values[field] ?? "";
  switch (field) {
    case "soc_start":
      return row(t("field_soc_start"), numberInput(field, value, onChange, 0, 100, "0.1"));
    case "soc_end":
      return row(t("field_soc_end"), numberInput(field, value, onChange, 0, 100, "0.1"));
    case "odometer_km":
      return row(t("field_odometer_km"), numberInput(field, value, onChange, 0, undefined, "0.1"));
    case "energy_billed_kwh":
      return row(
        t("field_energy_billed_kwh"),
        numberInput(field, value, onChange, 0, undefined, "0.001"),
      );
    case "cost":
      return row(t("field_cost"), numberInput(field, value, onChange, 0, undefined, "0.01"));
    case "charge_type":
      if (session.charge_type_source !== "heuristic") {
        return nothing;
      }
      return row(
        t("filter_charge_type"),
        html`<select
          @change=${(event: Event) => onChange(field, (event.target as HTMLSelectElement).value)}
        >
          <option value="" .selected=${value === ""}>${t("filter_all")}</option>
          <option value="ac" .selected=${value === "ac"}>${t("charge_type_ac")}</option>
          <option value="dc" .selected=${value === "dc"}>${t("charge_type_dc")}</option>
        </select>`,
      );
    case "address":
      return row(t("detail_address"), textInput(field, value, onChange));
    case "note":
      return row(t("detail_note"), textInput(field, value, onChange));
    case "provider":
      return row(t("detail_provider"), textInput(field, value, onChange));
    case "plug_end":
      if (session.plug_end !== null) {
        return nothing;
      }
      return row(
        t("detail_plug_end"),
        html`<input
          type="datetime-local"
          .value=${value}
          @input=${(event: Event) => onChange(field, (event.target as HTMLInputElement).value)}
        />`,
      );
    default:
      return nothing;
  }
}

export function renderEditFields(
  session: Session,
  fields: EditFieldName[],
  values: EditValues,
  onChange: (field: EditFieldName, value: string) => void,
  t: Translate,
): TemplateResult {
  return html`<div class="edit-fields">
    ${fields.map((field) => renderField(session, field, values, onChange, t))}
  </div>`;
}

export function renderVehicleSelect(
  vehicles: Vehicle[],
  value: string,
  onChange: (value: string) => void,
  t: Translate,
): TemplateResult {
  return html`<select
    @change=${(event: Event) => onChange((event.target as HTMLSelectElement).value)}
  >
    <option value="" .selected=${value === ""}>${t("edit_select_vehicle")}</option>
    ${vehicles.map(
      (vehicle) =>
        html`<option value=${vehicle.id} .selected=${vehicle.id === value}>
          ${vehicle.name}
        </option>`,
    )}
  </select>`;
}

// The payload for updateSession, built from what was actually typed. A
// blank input contributes nothing, so an untouched field is never cleared.
export function buildUpdatePayload(values: EditValues): SessionUpdate {
  const payload: SessionUpdate = {};
  if (values.soc_start) payload.soc_start = Number(values.soc_start);
  if (values.soc_end) payload.soc_end = Number(values.soc_end);
  if (values.odometer_km) payload.odometer_km = Number(values.odometer_km);
  if (values.energy_billed_kwh) payload.energy_billed_kwh = Number(values.energy_billed_kwh);
  if (values.cost) payload.cost = Number(values.cost);
  if (values.charge_type) payload.charge_type = values.charge_type as ChargeType;
  if (values.address) payload.address = values.address;
  if (values.note) payload.note = values.note;
  if (values.provider) payload.provider = values.provider;
  if (values.plug_end) payload.plug_end = new Date(values.plug_end).toISOString();
  return payload;
}

export function hasUpdatePayload(values: EditValues): boolean {
  return Object.keys(buildUpdatePayload(values)).length > 0;
}

export const editStyles = css`
  .edit-form {
    margin: 8px 0;
    padding: 12px 14px;
    background: var(--ev-head-bg);
    border: 1px solid var(--ev-line);
    border-radius: var(--ev-radius);
  }

  .edit-fields {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 8px 16px;
    margin: 8px 0;
  }

  .edit-row {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 0.9em;
  }

  .edit-row input,
  .edit-row select {
    padding: 6px 8px;
    background: var(--ev-surface);
    border: 1px solid var(--ev-line);
    border-radius: 8px;
    font: inherit;
    color: inherit;
  }

  .edit-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
  }

  .edit-vehicle {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  button.danger {
    border-color: var(--error-color, #db4437);
    color: var(--error-color, #db4437);
  }

  .edit-message {
    font-size: 0.85em;
  }

  .edit-message.error {
    color: var(--error-color, #db4437);
  }
`;
