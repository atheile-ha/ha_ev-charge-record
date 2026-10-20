"""Binary sensors that publish the state of the session capture."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import TITLE
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


class EvChargingProblemBinarySensor(BinarySensorEntity):
    """On while the wallbox or a vehicle reports a charging error.

    Belongs to the hub entry. source and vehicle_id name the error that arose
    last among those still reported.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, manager: SessionManager, entry_id: str) -> None:
        """Create the binary sensor."""
        self._manager = manager
        self._attr_unique_id = f"{entry_id}_problem"
        self._attr_translation_placeholders = {"title": TITLE}

    async def async_added_to_hass(self) -> None:
        """Follow published snapshots for as long as the entity exists."""
        self.async_on_remove(self._manager.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        """Write the new state."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return whether a charging error is reported."""
        return self._manager.snapshot.problem is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the source of the error and the vehicle it concerns."""
        problem = self._manager.snapshot.problem
        return {
            "source": problem.source if problem is not None else None,
            "vehicle_id": problem.vehicle_id if problem is not None else None,
        }


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
    async_add_entities([EvChargingProblemBinarySensor(manager, entry.entry_id)])
    for context in manager.vehicle_contexts:
        if not context.vehicle.active or context.vehicle.is_guest:
            continue
        async_add_entities(
            [EvChargingVehicleSessionBinarySensor(manager, context)],
            config_subentry_id=context.subentry_id,
        )
