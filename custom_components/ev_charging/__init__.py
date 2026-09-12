"""The ev_charging integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_VEHICLE_SEQUENCE, CONF_WALLBOX_SEQUENCE


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ev_charging from a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate the hub entry to the current schema."""
    if entry.version == 1 and entry.minor_version == 1:
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_WALLBOX_SEQUENCE: entry.data.get(CONF_WALLBOX_SEQUENCE, 0),
                CONF_VEHICLE_SEQUENCE: entry.data.get(CONF_VEHICLE_SEQUENCE, 0),
            },
            minor_version=2,
        )
    return True
