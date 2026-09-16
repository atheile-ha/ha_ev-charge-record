"""Tests for role resolution, unit detection, and state classification."""

from custom_components.ev_charging import resolver
from custom_components.ev_charging.const import (
    CHARGE_STATE_CHARGING,
    CHARGE_STATE_CONNECTED_IDLE,
    ERROR_CLASS_ERROR,
    ERROR_CLASS_OK,
    PLUG_STATE_CONNECTED,
)
from custom_components.ev_charging.models import EntityRole
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir


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


async def test_integration_meets_min_version_true_for_current_version(
    hass: HomeAssistant,
) -> None:
    """An installed integration at or above min_version passes (4.7, O20)."""
    from pytest_homeassistant_custom_component.common import MockModule, mock_integration

    mock_integration(hass, MockModule("openems", partial_manifest={"version": "1.7.2"}))

    assert await resolver.async_integration_meets_min_version(hass, "openems", "1.7.2") is True


async def test_integration_meets_min_version_false_when_too_old(hass: HomeAssistant) -> None:
    """An installed integration below min_version fails."""
    from pytest_homeassistant_custom_component.common import MockModule, mock_integration

    mock_integration(hass, MockModule("mbapi2020", partial_manifest={"version": "0.20.0"}))

    assert await resolver.async_integration_meets_min_version(hass, "mbapi2020", "0.29.2") is False


async def test_integration_meets_min_version_none_when_not_installed(
    hass: HomeAssistant,
) -> None:
    """A domain with no installed integration returns None, distinct from too old."""
    result = await resolver.async_integration_meets_min_version(hass, "openems", "1.7.2")
    assert result is None
