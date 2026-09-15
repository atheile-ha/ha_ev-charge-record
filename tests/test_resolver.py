"""Tests for role resolution, unit detection, and state classification."""

from pathlib import Path

from custom_components.ev_charging import resolver
from custom_components.ev_charging.const import (
    CHARGE_STATE_CHARGING,
    CHARGE_STATE_CONNECTED_IDLE,
    ERROR_CLASS_ERROR,
    ERROR_CLASS_OK,
    MAPPING_UNMAPPED,
    PLUG_STATE_CONNECTED,
)
from custom_components.ev_charging.models import EntityRole
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

PRESETS_DIR = Path(__file__).parent.parent / "custom_components" / "ev_charging" / "presets"


def test_unmapped_charge_state_defaults_to_connected_idle() -> None:
    """A vehicle charge state outside the mapping never becomes disconnected (I15)."""
    klass, mapped = resolver.classify_charge_state("some_new_code", {"0": CHARGE_STATE_CHARGING})

    assert klass == CHARGE_STATE_CONNECTED_IDLE
    assert mapped is False


def test_mapped_charge_state_is_used() -> None:
    """A mapped raw value resolves to its configured class."""
    klass, mapped = resolver.classify_charge_state("0", {"0": CHARGE_STATE_CHARGING})

    assert klass == CHARGE_STATE_CHARGING
    assert mapped is True


def test_unmapped_plug_state_stays_connected() -> None:
    """An unrecognized plug state never looks like a disconnect on its own."""
    klass, mapped = resolver.classify_plug_state("unexpected", {})

    assert klass == PLUG_STATE_CONNECTED
    assert mapped is False


def test_unmapped_error_state_is_never_an_error() -> None:
    """An unrecognized error-role state value is never treated as an error (E29)."""
    klass, mapped = resolver.classify_error_state("unexpected", {"4": ERROR_CLASS_ERROR})

    assert klass == ERROR_CLASS_OK
    assert mapped is False


def test_unmapped_charge_type_is_none() -> None:
    """An unmapped charge_type value stays undetermined rather than guessed."""
    assert resolver.classify_charge_type("5", {"6": "dc"}) is None
    assert resolver.classify_charge_type("6", {"6": "dc"}) == "dc"


def test_normalize_power_kw_converts_known_units() -> None:
    """Power values are normalized to kW for the recognized units."""
    assert resolver.normalize_power_kw(1500, "W") == 1.5
    assert resolver.normalize_power_kw(11, "kW") == 11


def test_normalize_power_kw_rejects_unknown_unit() -> None:
    """An unrecognized unit is never guessed at (5.3)."""
    assert resolver.normalize_power_kw(11, "hp") is None


def test_normalize_energy_kwh_converts_known_units() -> None:
    """Energy values are normalized to kWh for the recognized units."""
    assert resolver.normalize_energy_kwh(1000, "Wh") == 1.0


def test_normalize_distance_km_converts_known_units() -> None:
    """Distance values are normalized to km for the recognized units."""
    assert round(resolver.normalize_distance_km(1, "mi"), 6) == 1.609344


def test_unit_changed_detects_a_mismatch() -> None:
    """A live unit different from the one recorded at assignment is flagged (I13)."""
    role = EntityRole(entity_id="sensor.x", unit="kW")

    assert resolver.unit_changed(role, "W") is True
    assert resolver.unit_changed(role, "kW") is False


def test_unit_changed_is_false_without_a_recorded_unit() -> None:
    """A role without a numeric unit is never flagged."""
    role = EntityRole(entity_id="sensor.x", unit=None)

    assert resolver.unit_changed(role, "kW") is False


def test_mapping_from_rows_drops_unmapped_and_blank_rows() -> None:
    """Rows left at the unmapped sentinel, or without a raw value, are dropped."""
    rows = [
        {"raw_value": "5", "class": "connected"},
        {"raw_value": "7", "class": MAPPING_UNMAPPED},
        {"raw_value": "", "class": "connected"},
    ]

    assert resolver.mapping_from_rows(rows) == {"5": "connected"}


def test_build_mapping_rows_merges_existing_preset_and_discovered() -> None:
    """Existing entries win, then preset values, then newly discovered raw values."""
    rows = resolver.build_mapping_rows(
        existing={"5": "connected"},
        preset_values={"5": "not_connected", "7": "connected"},
        discovered={"7", "9"},
    )

    by_raw_value = {row["raw_value"]: row["class"] for row in rows}
    assert by_raw_value["5"] == "connected"
    assert by_raw_value["7"] == "connected"
    assert by_raw_value["9"] == MAPPING_UNMAPPED


def test_format_preset_reference_includes_codes_and_cable_note() -> None:
    """The reference text lists every code and appends the cable-variant note."""
    text = resolver.format_preset_reference(
        {
            "codes": [{"code": 5, "meaning": "connected", "class": "connected"}],
            "cable_variant_note": "fixed cable note",
        }
    )

    assert "5 = connected (connected)" in text
    assert "fixed cable note" in text


def test_openems_keba_preset_has_both_tables() -> None:
    """The bundled OpenEMS/KEBA preset carries the plug_state and error tables."""
    preset = resolver.load_preset(PRESETS_DIR / "openems_keba.json")

    assert preset["platform"] == "openems"
    assert {entry["code"] for entry in preset["plug_state"]["codes"]} == {0, 1, 3, 5, 7}
    assert {entry["code"] for entry in preset["error"]["codes"]} == {0, 1, 2, 3, 4, 5}


def test_mercedes_me_preset_maps_codes_to_classes() -> None:
    """The bundled Mercedes Me preset maps every documented code to a class."""
    preset = resolver.load_preset(PRESETS_DIR / "mercedes_me.json")

    assert preset["platform"] == "mercedes_me"
    assert preset["charge_state"]["values"]["11"] == "charging"
    assert preset["charge_type"]["values"]["11"] == "dc"
    assert preset["charge_type"]["values"]["13"] == "ac"
    assert "5" not in preset["charge_type"]["values"]


def test_find_preset_matches_by_platform() -> None:
    """find_preset returns the preset whose platform matches, or None."""
    assert resolver.find_preset(PRESETS_DIR, "openems")["platform"] == "openems"
    assert resolver.find_preset(PRESETS_DIR, "unknown_platform") is None
    assert resolver.find_preset(PRESETS_DIR, None) is None


async def test_resolve_entity_id_prefers_registry_entry(hass: HomeAssistant) -> None:
    """A role with a registry entry resolves via the registry, not the stored entity_id."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get_or_create("sensor", "test", "unique_1")
    role = EntityRole(entity_id="sensor.stale", registry_entry_id=entity_entry.id)

    assert resolver.resolve_entity_id(hass, role) == entity_entry.entity_id


async def test_resolve_entity_id_falls_back_without_a_registry_entry(
    hass: HomeAssistant,
) -> None:
    """A role without a registry entry resolves via the stored entity_id (4.8)."""
    role = EntityRole(entity_id="sensor.no_registry")

    assert resolver.resolve_entity_id(hass, role) == "sensor.no_registry"


async def test_resolve_entity_id_returns_none_for_a_removed_registry_entry(
    hass: HomeAssistant,
) -> None:
    """A role whose registry entry no longer exists resolves to nothing."""
    role = EntityRole(entity_id="sensor.gone", registry_entry_id="missing-id")

    assert resolver.resolve_entity_id(hass, role) is None


async def test_build_role_captures_registry_entry_and_unit(hass: HomeAssistant) -> None:
    """build_role captures the registry entry id and the current unit (4.8, 5.3)."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get_or_create("sensor", "test", "unique_2")
    hass.states.async_set(entity_entry.entity_id, "11", {"unit_of_measurement": "kW"})

    role = resolver.build_role(hass, entity_entry.entity_id)

    assert role.registry_entry_id == entity_entry.id
    assert role.unit == "kW"


async def test_build_role_without_a_registry_entry(hass: HomeAssistant) -> None:
    """build_role falls back to entity_id only when there is no registry entry (4.8)."""
    hass.states.async_set("sensor.plain", "1")

    role = resolver.build_role(hass, "sensor.plain")

    assert role.registry_entry_id is None
    assert role.entity_id == "sensor.plain"


async def test_check_role_unit_creates_and_clears_issue(hass: HomeAssistant) -> None:
    """check_role_unit creates the issue on a mismatch and clears it once resolved."""
    hass.states.async_set("sensor.power", "1500", {"unit_of_measurement": "W"})
    role = EntityRole(entity_id="sensor.power", unit="kW")

    resolver.check_role_unit(
        hass,
        role,
        issue_id="test_issue",
        translation_key="role_unit_changed",
        translation_placeholders={"role": "charge_power", "subentry_title": "Carport"},
    )
    assert ir.async_get(hass).async_get_issue("ev_charging", "test_issue") is not None

    hass.states.async_set("sensor.power", "1.5", {"unit_of_measurement": "kW"})
    resolver.check_role_unit(
        hass,
        role,
        issue_id="test_issue",
        translation_key="role_unit_changed",
        translation_placeholders={"role": "charge_power", "subentry_title": "Carport"},
    )
    assert ir.async_get(hass).async_get_issue("ev_charging", "test_issue") is None


async def test_track_role_registry_reacts_to_removal(hass: HomeAssistant) -> None:
    """The registry tracker calls on_removed when the entity is removed (4.8)."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get_or_create("sensor", "test", "unique_3")
    role = EntityRole(entity_id=entity_entry.entity_id, registry_entry_id=entity_entry.id)
    removed = []

    unsub = resolver.async_track_role_registry(hass, role, on_removed=lambda: removed.append(True))
    assert unsub is not None

    registry.async_remove(entity_entry.entity_id)
    await hass.async_block_till_done()

    assert removed == [True]
    unsub()


async def test_track_role_registry_calls_on_removed_immediately_if_already_gone(
    hass: HomeAssistant,
) -> None:
    """A role pointing at an already-missing registry entry is reported removed right away."""
    role = EntityRole(entity_id="sensor.gone", registry_entry_id="missing-id")
    removed = []

    unsub = resolver.async_track_role_registry(hass, role, on_removed=lambda: removed.append(True))

    assert unsub is None
    assert removed == [True]


async def test_track_role_registry_survives_a_rename(hass: HomeAssistant) -> None:
    """A renamed entity keeps being tracked under its new entity_id (4.8)."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get_or_create("sensor", "test", "unique_4")
    role = EntityRole(entity_id=entity_entry.entity_id, registry_entry_id=entity_entry.id)
    removed = []

    unsub = resolver.async_track_role_registry(hass, role, on_removed=lambda: removed.append(True))
    registry.async_update_entity(entity_entry.entity_id, new_entity_id="sensor.renamed")
    await hass.async_block_till_done()

    registry.async_remove("sensor.renamed")
    await hass.async_block_till_done()

    assert removed == [True]
    unsub()


async def test_query_recorder_states_returns_distinct_known_states(
    hass: HomeAssistant,
) -> None:
    """The recorder query returns the distinct raw states, excluding unknown/unavailable (4.7).

    The recorder itself is exercised manually in Home Assistant per the stage's
    acceptance criteria; here the query's own filtering runs against a stubbed
    recorder history so the test stays fast and independent of the recorder setup.
    """
    from unittest.mock import MagicMock, patch

    from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

    fake_states = [
        MagicMock(state="plugged_on_wallbox_and_locked__not_ev_"),
        MagicMock(state="plugged_on_wallbox_and_vehicle"),
        MagicMock(state="plugged_on_wallbox_and_vehicle"),
        MagicMock(state=STATE_UNKNOWN),
        MagicMock(state=STATE_UNAVAILABLE),
    ]

    with patch(
        "homeassistant.components.recorder.history.state_changes_during_period",
        return_value={"sensor.plug_state": fake_states},
    ) as mocked:
        states = await resolver.async_query_recorder_states(hass, "sensor.plug_state")

    assert states == {"plugged_on_wallbox_and_locked__not_ev_", "plugged_on_wallbox_and_vehicle"}
    assert mocked.call_args.kwargs["no_attributes"] is True
