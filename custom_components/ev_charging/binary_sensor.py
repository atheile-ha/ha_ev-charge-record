"""Binary sensors that publish the state of the session capture."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .sensor import EvChargingEntity
from .session_manager import SessionManager

if TYPE_CHECKING:
    from . import EvChargingConfigEntry


class EvChargingSessionBinarySensor(EvChargingEntity, BinarySensorEntity):
    """On from the moment a charging session is recognized until it is written."""

    _attr_translation_key = "wallbox_session"

    def __init__(self, manager: SessionManager, entry_id: str) -> None:
        """Create the binary sensor."""
        super().__init__(manager, entry_id, "wallbox_session")

    @property
    def is_on(self) -> bool:
        """Return whether a session exists, including a candidate."""
        return self._manager.snapshot.session_active


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EvChargingConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensors of the session capture."""
    manager = entry.runtime_data.manager
    if manager is None:
        return
    async_add_entities([EvChargingSessionBinarySensor(manager, entry.entry_id)])
