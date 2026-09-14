"""Tests for setting up, unloading and removing the ev_charging config entry."""

from custom_components.ev_charging.const import (
    DOMAIN,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

CURRENT_DATA = {
    "wallbox_seq": 0,
    "vehicle_seq": 0,
    "update_interval_s": 30,
    "solar_valuation": "feed_in_tariff",
    "geocoding_enabled": True,
    "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
    "geocoding_contact": None,
    "estimate_uncertain_threshold_pct": 5,
}


async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """The config entry loads and unloads again."""
    entry = MockConfigEntry(
        domain=DOMAIN, title=TITLE, data=CURRENT_DATA, version=2, minor_version=1
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
        domain=DOMAIN, title=TITLE, data=CURRENT_DATA, version=2, minor_version=1
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

    assert entry.version == 2
    assert entry.minor_version == 1
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


async def test_setup_creates_no_entities(hass: HomeAssistant) -> None:
    """This stage has no platforms, so no entities appear."""
    entry = MockConfigEntry(
        domain=DOMAIN, title=TITLE, data=CURRENT_DATA, version=2, minor_version=1
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert [state.entity_id for state in hass.states.async_all()] == []
