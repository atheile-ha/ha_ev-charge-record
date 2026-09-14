"""The ev_charging integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_VEHICLE_SEQUENCE,
    CONF_WALLBOX_SEQUENCE,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
)
from .models import HubSettings, Vehicle, Wallbox

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ev_charging from a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate the hub entry and its subentries to the current schema."""
    if entry.version == 1:
        from_version = f"{entry.version}.{entry.minor_version}"
        for subentry in entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_WALLBOX:
                wallbox = Wallbox.from_dict(subentry.data)
                hass.config_entries.async_update_subentry(entry, subentry, data=wallbox.to_dict())
            elif subentry.subentry_type == SUBENTRY_TYPE_VEHICLE:
                vehicle = Vehicle.from_dict(subentry.data)
                hass.config_entries.async_update_subentry(entry, subentry, data=vehicle.to_dict())

        data = {
            CONF_WALLBOX_SEQUENCE: entry.data.get(CONF_WALLBOX_SEQUENCE, 0),
            CONF_VEHICLE_SEQUENCE: entry.data.get(CONF_VEHICLE_SEQUENCE, 0),
            **HubSettings.from_dict(entry.data).to_dict(),
        }
        hass.config_entries.async_update_entry(entry, data=data, version=2, minor_version=1)
        _LOGGER.info(
            "Migrated ev_charging config entry %s from version %s to 2.1",
            entry.entry_id,
            from_version,
        )
    return True
