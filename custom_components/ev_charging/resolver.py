"""Role resolution, unit detection, and entity registry observation."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_registry import EventEntityRegistryUpdatedData
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from .const import (
    CHARGE_STATE_DEFAULT,
    DISTANCE_UNIT_FACTORS_TO_KM,
    DOMAIN,
    ENERGY_UNIT_FACTORS_TO_KWH,
    ERROR_CLASS_OK,
    MAPPING_UNMAPPED,
    PLUG_STATE_CONNECTED,
    POWER_UNIT_FACTORS_TO_KW,
    RECORDER_STATE_LOOKBACK_DAYS,
)
from .models import EntityRole

_LOGGER = logging.getLogger(__name__)


def build_role(hass: HomeAssistant, entity_id: str | None) -> EntityRole | None:
    """Build a role from a freshly selected entity_id (5.1, 5.2, 4.8).

    Captures the registry entry id, when one exists, and the entity's
    current unit_of_measurement.
    """
    if not entity_id:
        return None
    entry = er.async_get(hass).async_get(entity_id)
    state = hass.states.get(entity_id)
    unit = state.attributes.get("unit_of_measurement") if state is not None else None
    return EntityRole(
        entity_id=entity_id,
        registry_entry_id=entry.id if entry is not None else None,
        unit=unit,
    )


def resolve_entity_id(hass: HomeAssistant, role: EntityRole | None) -> str | None:
    """Return a role's current entity_id.

    Prefers the registry entry id (E15). Falls back to the stored entity_id
    for entities without a registry entry (4.8). Returns None if a registry
    entry id is stored but the entry no longer exists.
    """
    if role is None:
        return None
    if role.registry_entry_id is not None:
        entry = er.async_get(hass).async_get(role.registry_entry_id)
        return entry.entity_id if entry is not None else None
    return role.entity_id


def resolve_platform(hass: HomeAssistant, role: EntityRole | None) -> str | None:
    """Return the integration domain backing a role's entity, if known."""
    if role is None or role.registry_entry_id is None:
        return None
    entry = er.async_get(hass).async_get(role.registry_entry_id)
    return entry.platform if entry is not None else None


def resolve_current_unit(hass: HomeAssistant, role: EntityRole | None) -> str | None:
    """Return the current unit_of_measurement of a role's entity, if any."""
    entity_id = resolve_entity_id(hass, role)
    if entity_id is None:
        return None
    state = hass.states.get(entity_id)
    if state is None:
        return None
    return state.attributes.get("unit_of_measurement")


def unit_changed(role: EntityRole | None, current_unit: str | None) -> bool:
    """Return whether current_unit differs from the unit recorded at assignment (I13)."""
    if role is None or role.unit is None:
        return False
    return current_unit != role.unit


def check_role_unit(
    hass: HomeAssistant,
    role: EntityRole | None,
    *,
    issue_id: str,
    translation_key: str,
    translation_placeholders: dict[str, str],
) -> None:
    """Create or clear the unit-changed repair issue for a numeric role."""
    if role is not None and role.unit is not None:
        current_unit = resolve_current_unit(hass, role)
        if current_unit is not None and unit_changed(role, current_unit):
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=translation_key,
                translation_placeholders=translation_placeholders,
            )
            return
    ir.async_delete_issue(hass, DOMAIN, issue_id)


def _normalize(value: float, unit: str | None, factors: dict[str, float]) -> float | None:
    """Convert value to the canonical unit for factors, or None if unrecognized."""
    if unit is None:
        return None
    factor = factors.get(unit)
    return value * factor if factor is not None else None


def normalize_power_kw(value: float, unit: str | None) -> float | None:
    """Convert a power value to kW."""
    return _normalize(value, unit, POWER_UNIT_FACTORS_TO_KW)


def normalize_energy_kwh(value: float, unit: str | None) -> float | None:
    """Convert an energy value to kWh."""
    return _normalize(value, unit, ENERGY_UNIT_FACTORS_TO_KWH)


def normalize_distance_km(value: float, unit: str | None) -> float | None:
    """Convert a distance value to km."""
    return _normalize(value, unit, DISTANCE_UNIT_FACTORS_TO_KM)


def classify_state(raw_state: str, mapping: dict[str, str], *, default: str) -> tuple[str, bool]:
    """Classify a raw state value using a mapping.

    Returns the class and whether the value was found in the mapping. An
    unmapped value falls back to default instead of raising.
    """
    if raw_state in mapping:
        return mapping[raw_state], True
    return default, False


def classify_charge_state(raw_state: str, mapping: dict[str, str]) -> tuple[str, bool]:
    """Classify a vehicle's raw charge state into one of the four classes (I15)."""
    return classify_state(raw_state, mapping, default=CHARGE_STATE_DEFAULT)


def classify_plug_state(raw_state: str, mapping: dict[str, str]) -> tuple[str, bool]:
    """Classify the wallbox's raw plug state.

    An unmapped value stays connected, so an unrecognized state never ends a
    session on its own.
    """
    return classify_state(raw_state, mapping, default=PLUG_STATE_CONNECTED)


def classify_error_state(raw_state: str, mapping: dict[str, str]) -> tuple[str, bool]:
    """Classify a raw error-role state value. An unmapped value is never an error (E29)."""
    return classify_state(raw_state, mapping, default=ERROR_CLASS_OK)


def classify_charge_type(raw_state: str, mapping: dict[str, str]) -> str | None:
    """Classify a raw charge_type value into ac or dc, or None if unmapped."""
    return mapping.get(raw_state)


@callback
def async_track_role_registry(
    hass: HomeAssistant,
    role: EntityRole,
    *,
    on_removed: Callable[[], None],
) -> Callable[[], None] | None:
    """Track entity registry changes for a role backed by a registry entry (4.8).

    Reacts to removal by calling on_removed and logs a rename at INFO level,
    re-subscribing under the new entity_id. Returns None, calling on_removed
    immediately, if the registry entry is already gone. Returns None without
    tracking anything for a role that has no registry entry to track.
    """
    if role.registry_entry_id is None:
        return None

    entry = er.async_get(hass).async_get(role.registry_entry_id)
    if entry is None:
        on_removed()
        return None

    unsub_holder: list[Callable[[], None]] = []

    @callback
    def _handle(event: Event[EventEntityRegistryUpdatedData]) -> None:
        if event.data["action"] == "remove":
            on_removed()
            return
        if event.data["action"] == "update" and "old_entity_id" in event.data:
            _LOGGER.info(
                "Entity for role %s renamed from %s to %s",
                role.registry_entry_id,
                event.data["old_entity_id"],
                event.data["entity_id"],
            )
            unsub_holder[0]()
            unsub_holder[0] = async_track_entity_registry_updated_event(
                hass, [event.data["entity_id"]], _handle
            )

    unsub_holder.append(async_track_entity_registry_updated_event(hass, [entry.entity_id], _handle))

    def _unsub() -> None:
        unsub_holder[0]()

    return _unsub


async def async_query_recorder_states(hass: HomeAssistant, entity_id: str) -> set[str]:
    """Return the distinct raw states observed for entity_id over the trailing period.

    Runs the blocking recorder query in the executor.
    """
    from homeassistant.components.recorder import history

    end_time = dt_util.utcnow()
    start_time = end_time - timedelta(days=RECORDER_STATE_LOOKBACK_DAYS)

    def _query() -> set[str]:
        changes = history.state_changes_during_period(
            hass,
            start_time,
            end_time,
            entity_id,
            no_attributes=True,
            include_start_time_state=False,
        )
        return {
            state.state
            for state in changes.get(entity_id, [])
            if state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
        }

    return await hass.async_add_executor_job(_query)


def load_preset(path: Path) -> dict[str, Any]:
    """Read and parse a bundled preset JSON file.

    Blocking; call via the executor.
    """
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def format_preset_reference(preset_role: dict[str, Any]) -> str:
    """Format a preset role's reference code table as readable text for a dialog."""
    lines = [
        f"{entry['code']} = {entry['meaning']} ({entry['class']})"
        for entry in preset_role.get("codes", [])
    ]
    note = preset_role.get("cable_variant_note")
    if note:
        lines.append(note)
    return "\n".join(lines)


def build_mapping_rows(
    *,
    existing: dict[str, str],
    preset_values: dict[str, str] | None,
    discovered: set[str],
) -> list[dict[str, str]]:
    """Merge an existing mapping, direct preset values, and recorder-discovered values.

    Existing entries take priority, then preset entries, then newly
    discovered values, which start out as MAPPING_UNMAPPED.
    """
    rows: dict[str, str] = dict(existing)
    for raw_value, klass in (preset_values or {}).items():
        rows.setdefault(raw_value, klass)
    for raw_value in discovered:
        rows.setdefault(raw_value, MAPPING_UNMAPPED)
    return [{"raw_value": raw_value, "class": klass} for raw_value, klass in rows.items()]


def mapping_from_rows(rows: list[dict[str, Any]]) -> dict[str, str]:
    """Convert submitted mapping rows back into a raw_value-to-class mapping.

    Rows left at MAPPING_UNMAPPED, or with an empty raw value, are dropped.
    """
    mapping: dict[str, str] = {}
    for row in rows:
        raw_value = str(row.get("raw_value", "")).strip()
        klass = row.get("class")
        if not raw_value or not klass or klass == MAPPING_UNMAPPED:
            continue
        mapping[raw_value] = klass
    return mapping


def find_preset(presets_dir: Path, platform: str | None) -> dict[str, Any] | None:
    """Return the bundled preset matching platform, if any.

    Blocking; call via the executor.
    """
    if platform is None:
        return None
    for preset_path in sorted(presets_dir.glob("*.json")):
        data = load_preset(preset_path)
        if data.get("platform") == platform:
            return data
    return None
