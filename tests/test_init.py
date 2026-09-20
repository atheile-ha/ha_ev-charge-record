"""Tests for setting up, unloading and removing the ev_charging config entry."""

import logging

import pytest
from custom_components.ev_charging import problems
from custom_components.ev_charging.const import (
    DOMAIN,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
)
from custom_components.ev_charging.models import EntityRole, Vehicle, Wallbox
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    MockModule,
    mock_integration,
)

CURRENT_DATA = {
    "wallbox_seq": 0,
    "vehicle_seq": 0,
    "update_interval_s": 30,
    "solar_valuation": "feed_in_tariff",
    "geocoding_enabled": True,
    "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
    "geocoding_contact": None,
    "estimate_uncertain_threshold_pct": 5,
    "grid_power": None,
    "grid_power_inverted": False,
    "grid_import": None,
    "grid_export": None,
    "price_grid": None,
    "price_grid_fixed": None,
    "price_feed_in": None,
    "price_feed_in_fixed": None,
}


async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """The config entry loads and unloads again."""
    entry = MockConfigEntry(
        domain=DOMAIN, title=TITLE, data=CURRENT_DATA, version=3, minor_version=1
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_remove_entry(hass: HomeAssistant) -> None:
    """Removing the config entry leaves nothing behind."""
    entry = MockConfigEntry(
        domain=DOMAIN, title=TITLE, data=CURRENT_DATA, version=3, minor_version=1
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_remove(entry.entry_id) == {"require_restart": False}
    await hass.async_block_till_done()

    assert hass.config_entries.async_entries(DOMAIN) == []
    assert DOMAIN not in hass.data


async def test_migrate_entry_adds_hub_settings(hass: HomeAssistant) -> None:
    """An entry from before the global settings existed is migrated on setup."""
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data={}, version=1, minor_version=1)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 5
    assert entry.minor_version == 1
    assert entry.data == CURRENT_DATA


async def test_migrate_entry_v2_adds_grid_and_price_roles(hass: HomeAssistant) -> None:
    """An entry from before entity roles existed gains the new role fields."""
    old_data = {
        "wallbox_seq": 0,
        "vehicle_seq": 0,
        "update_interval_s": 30,
        "solar_valuation": "feed_in_tariff",
        "geocoding_enabled": True,
        "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
        "geocoding_contact": None,
        "estimate_uncertain_threshold_pct": 5,
    }
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data=old_data, version=2, minor_version=1)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 5
    assert entry.data == CURRENT_DATA


async def test_migrate_entry_updates_wallbox_subentry(hass: HomeAssistant) -> None:
    """A wallbox subentry loses default_vehicle_id and gains identification_window_s."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data={"wallbox_seq": 1, "vehicle_seq": 0},
        version=1,
        minor_version=2,
        subentries_data=[
            {
                "data": {
                    "id": "wb001",
                    "name": "Carport",
                    "current_type": "ac",
                    "max_power_kw": 11.0,
                    "power_threshold_kw": 0.5,
                    "start_debounce_s": 20,
                    "default_vehicle_id": None,
                },
                "subentry_type": SUBENTRY_TYPE_WALLBOX,
                "title": "Carport",
                "unique_id": None,
            }
        ],
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    subentry = next(iter(entry.subentries.values()))
    assert "default_vehicle_id" not in subentry.data
    assert subentry.data["identification_window_s"] == 15
    assert subentry.data["start_debounce_s"] == 20


async def test_migrate_entry_updates_vehicle_subentry(hass: HomeAssistant) -> None:
    """A vehicle subentry loses static_price/solar_valuation, gains manufacturer/model."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data={"wallbox_seq": 0, "vehicle_seq": 1},
        version=1,
        minor_version=2,
        subentries_data=[
            {
                "data": {
                    "id": "v001",
                    "name": "GLB 250+ EQ",
                    "active": True,
                    "is_guest": False,
                    "vin": None,
                    "capacity_kwh": 85.0,
                    "cost_mode": "dynamic",
                    "static_price": None,
                    "solar_valuation": "feed_in_tariff",
                    "cards": [{"uid": "ABC123", "label": "Karte GLB", "active": True}],
                },
                "subentry_type": SUBENTRY_TYPE_VEHICLE,
                "title": "GLB 250+ EQ",
                "unique_id": None,
            }
        ],
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    subentry = next(iter(entry.subentries.values()))
    assert "static_price" not in subentry.data
    assert "solar_valuation" not in subentry.data
    assert subentry.data["manufacturer"] is None
    assert subentry.data["model"] is None
    assert subentry.data["cards"][0]["type"] == "rfid"


def _wallbox_subentry_data(*, charge_power: EntityRole) -> dict:
    return Wallbox(
        id="wb001",
        name="Carport",
        current_type="ac",
        max_power_kw=11.0,
        charge_power=charge_power,
        plug_state=EntityRole(entity_id="sensor.wallbox_plug_state"),
        energy_total=EntityRole(entity_id="sensor.wallbox_energy_total", unit="kWh"),
    ).to_dict()


async def test_removed_role_entity_creates_repair_issue(hass: HomeAssistant) -> None:
    """Removing a role's registered entity creates a repair issue on setup."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get_or_create("sensor", "test", "wallbox_power_unique")
    hass.states.async_set(entity_entry.entity_id, "1.5", {"unit_of_measurement": "kW"})

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=CURRENT_DATA,
        version=3,
        minor_version=1,
        subentries_data=[
            {
                "data": _wallbox_subentry_data(
                    charge_power=EntityRole(
                        entity_id=entity_entry.entity_id,
                        registry_entry_id=entity_entry.id,
                        unit="kW",
                    )
                ),
                "subentry_type": SUBENTRY_TYPE_WALLBOX,
                "title": "Carport",
                "unique_id": None,
            }
        ],
    )
    entry.add_to_hass(hass)
    subentry = next(iter(entry.subentries.values()))

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry.async_remove(entity_entry.entity_id)
    await hass.async_block_till_done()

    issue_id = problems.role_removed_issue_id(subentry.subentry_id, "charge_power")
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is not None


async def test_unit_change_creates_repair_issue_on_setup(hass: HomeAssistant) -> None:
    """A role whose live unit no longer matches the recorded one is flagged on setup."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get_or_create("sensor", "test", "wallbox_power_unique2")
    # The entity now reports W, but the role was assigned while it reported kW.
    hass.states.async_set(entity_entry.entity_id, "1500", {"unit_of_measurement": "W"})

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=CURRENT_DATA,
        version=3,
        minor_version=1,
        subentries_data=[
            {
                "data": _wallbox_subentry_data(
                    charge_power=EntityRole(
                        entity_id=entity_entry.entity_id,
                        registry_entry_id=entity_entry.id,
                        unit="kW",
                    )
                ),
                "subentry_type": SUBENTRY_TYPE_WALLBOX,
                "title": "Carport",
                "unique_id": None,
            }
        ],
    )
    entry.add_to_hass(hass)
    subentry = next(iter(entry.subentries.values()))

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    issue_id = problems.role_unit_changed_issue_id(subentry.subentry_id, "charge_power")
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is not None


async def test_setup_creates_no_entities(hass: HomeAssistant) -> None:
    """This stage has no platforms, so no entities appear."""
    entry = MockConfigEntry(
        domain=DOMAIN, title=TITLE, data=CURRENT_DATA, version=3, minor_version=1
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert [state.entity_id for state in hass.states.async_all()] == []


async def test_migrate_entry_discards_stored_state_mappings(hass: HomeAssistant) -> None:
    """v3 to v4 drops the old per-value mappings; mapping_id defaults to unset."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=CURRENT_DATA,
        version=3,
        minor_version=1,
        subentries_data=[
            {
                "data": {
                    **_wallbox_subentry_data(
                        charge_power=EntityRole(entity_id="sensor.wallbox_power")
                    ),
                    "plug_state_mapping": {"5": "connected"},
                    "error_mapping": {"4": "error"},
                },
                "subentry_type": SUBENTRY_TYPE_WALLBOX,
                "title": "Carport",
                "unique_id": None,
            },
            {
                "data": {
                    **Vehicle(id="v001", name="GLB 250+ EQ", capacity_kwh=85.0).to_dict(),
                    "charge_state_mapping": {"0": "charging"},
                    "charge_type_mapping": {"13": "ac"},
                },
                "subentry_type": SUBENTRY_TYPE_VEHICLE,
                "title": "GLB 250+ EQ",
                "unique_id": None,
            },
        ],
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 5
    wallbox_data = next(
        sub.data for sub in entry.subentries.values() if sub.subentry_type == SUBENTRY_TYPE_WALLBOX
    )
    vehicle_data = next(
        sub.data for sub in entry.subentries.values() if sub.subentry_type == SUBENTRY_TYPE_VEHICLE
    )
    assert "plug_state_mapping" not in wallbox_data
    assert "error_mapping" not in wallbox_data
    assert wallbox_data["mapping_id"] is None
    assert "charge_state_mapping" not in vehicle_data
    assert "charge_type_mapping" not in vehicle_data
    assert vehicle_data["mapping_id"] is None


async def test_migrate_entry_v4_adds_the_direct_read_settings_once(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """v4 to v5 gives the wallbox its settings for reading the register, off, and runs once."""
    caplog.set_level(logging.INFO)
    wallbox = _wallbox_subentry_data(charge_power=EntityRole(entity_id="sensor.wallbox_power"))
    for key in (
        "host",
        "port",
        "unit_id",
        "identification_from_register",
    ):
        del wallbox[key]
    wallbox["mapping_id"] = "openems_keba_p40"
    vehicle = Vehicle(id="v001", name="GLB 250+ EQ", capacity_kwh=85.0).to_dict()
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=CURRENT_DATA,
        version=4,
        minor_version=1,
        subentries_data=[
            {
                "data": wallbox,
                "subentry_type": SUBENTRY_TYPE_WALLBOX,
                "title": "Carport",
                "unique_id": None,
            },
            {
                "data": vehicle,
                "subentry_type": SUBENTRY_TYPE_VEHICLE,
                "title": "GLB 250+ EQ",
                "unique_id": None,
            },
        ],
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 5
    wallbox_data = next(
        sub.data for sub in entry.subentries.values() if sub.subentry_type == SUBENTRY_TYPE_WALLBOX
    )
    assert "direct_read_enabled" not in wallbox_data
    assert wallbox_data["host"] is None
    assert wallbox_data["port"] == 502
    assert wallbox_data["unit_id"] == 255
    assert wallbox_data["identification_from_register"] is False
    assert wallbox_data["mapping_id"] == "openems_keba_p40"
    assert wallbox_data["name"] == "Carport"
    vehicle_data = next(
        sub.data for sub in entry.subentries.values() if sub.subentry_type == SUBENTRY_TYPE_VEHICLE
    )
    assert dict(vehicle_data) == vehicle

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    migrations = [message for message in caplog.messages if "to 5.1" in message]
    assert len(migrations) == 1


async def test_mapping_source_below_min_version_creates_repair_issue(hass: HomeAssistant) -> None:
    """A chosen device whose source integration fell below min_version is flagged (4.7, O20)."""
    mock_integration(hass, MockModule("openems", partial_manifest={"version": "1.0.0"}))
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=CURRENT_DATA,
        version=3,
        minor_version=1,
        subentries_data=[
            {
                "data": {
                    **_wallbox_subentry_data(
                        charge_power=EntityRole(entity_id="sensor.wallbox_power")
                    ),
                    "mapping_id": "openems_keba_p40",
                },
                "subentry_type": SUBENTRY_TYPE_WALLBOX,
                "title": "Carport",
                "unique_id": None,
            }
        ],
    )
    entry.add_to_hass(hass)
    subentry = next(iter(entry.subentries.values()))

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    issue_id = problems.mapping_source_below_min_version_issue_id(subentry.subentry_id)
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is not None


async def test_mapping_source_at_min_version_creates_no_repair_issue(hass: HomeAssistant) -> None:
    """No issue is created once the source integration meets min_version again."""
    mock_integration(hass, MockModule("openems", partial_manifest={"version": "1.7.2"}))
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=CURRENT_DATA,
        version=3,
        minor_version=1,
        subentries_data=[
            {
                "data": {
                    **_wallbox_subentry_data(
                        charge_power=EntityRole(entity_id="sensor.wallbox_power")
                    ),
                    "mapping_id": "openems_keba_p40",
                },
                "subentry_type": SUBENTRY_TYPE_WALLBOX,
                "title": "Carport",
                "unique_id": None,
            }
        ],
    )
    entry.add_to_hass(hass)
    subentry = next(iter(entry.subentries.values()))

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    issue_id = problems.mapping_source_below_min_version_issue_id(subentry.subentry_id)
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None
