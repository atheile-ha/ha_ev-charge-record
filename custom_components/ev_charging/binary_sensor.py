"""Binary sensors that publish the state of the session capture."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .sensor import EvChargingEntity, EvChargingVehicleEntity
from .session_manager import SessionManager, VehicleContext

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


class EvChargingVehicleSessionBinarySensor(EvChargingVehicleEntity, BinarySensorEntity):
    """On while a vehicle's own charging session is running, independent of the wallbox."""

    _attr_translation_key = "vehicle_session_active"

    def __init__(self, manager: SessionManager, context: VehicleContext) -> None:
        """Create the binary sensor."""
        super().__init__(manager, context, "session_active")

    @property
    def is_on(self) -> bool:
        """Return whether this vehicle's own session is active."""
        snapshot = self._snapshot
        return snapshot is not None and snapshot.session_active


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EvChargingConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensors of the session capture."""
    manager = entry.runtime_data.manager
    if manager is None:
        return
    async_add_entities(
        [EvChargingSessionBinarySensor(manager, entry.entry_id)],
        config_subentry_id=manager.wallbox_subentry_id,
    )
    for context in manager.vehicle_contexts:
        if not context.vehicle.active:
            continue
        async_add_entities(
            [EvChargingVehicleSessionBinarySensor(manager, context)],
            config_subentry_id=context.subentry_id,
        )
