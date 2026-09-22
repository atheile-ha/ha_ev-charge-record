"""Sensors that publish the state of the session capture."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import CHARGE_STATE_CLASSES, LOCATIONS, SESSION_STATES
from .session_manager import SessionManager, VehicleContext, VehicleSnapshot, WallboxSnapshot

if TYPE_CHECKING:
    from . import EvChargingConfigEntry


@dataclass(frozen=True, kw_only=True)
class EvChargingSensorDescription(SensorEntityDescription):
    """A sensor and the way its value is taken from the published snapshot."""

    value_fn: Callable[[WallboxSnapshot], StateType | datetime]
    per_currency: bool = False
    per_kwh: bool = False


SENSORS: tuple[EvChargingSensorDescription, ...] = (
    EvChargingSensorDescription(
        key="wallbox_state",
        translation_key="wallbox_state",
        device_class=SensorDeviceClass.ENUM,
        options=list(SESSION_STATES),
        value_fn=lambda snapshot: snapshot.state,
    ),
    EvChargingSensorDescription(
        key="active_vehicle",
        translation_key="active_vehicle",
        value_fn=lambda snapshot: snapshot.active_vehicle,
    ),
    EvChargingSensorDescription(
        key="session_cost",
        translation_key="session_cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        per_currency=True,
        value_fn=lambda snapshot: snapshot.cost,
    ),
    EvChargingSensorDescription(
        key="session_energy_grid",
        translation_key="session_energy_grid",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        value_fn=lambda snapshot: snapshot.energy_grid_kwh,
    ),
    EvChargingSensorDescription(
        key="session_energy_solar",
        translation_key="session_energy_solar",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        value_fn=lambda snapshot: snapshot.energy_solar_kwh,
    ),
    EvChargingSensorDescription(
        key="price_effective",
        translation_key="price_effective",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        per_currency=True,
        per_kwh=True,
        value_fn=lambda snapshot: snapshot.effective_price,
    ),
    EvChargingSensorDescription(
        key="open_followups",
        translation_key="open_followups",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda snapshot: snapshot.open_followups,
    ),
    EvChargingSensorDescription(
        key="active_vehicle_soc",
        translation_key="active_vehicle_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.vehicle_soc,
    ),
    EvChargingSensorDescription(
        key="active_vehicle_soc_target",
        translation_key="active_vehicle_soc_target",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.vehicle_soc_target,
    ),
    EvChargingSensorDescription(
        key="active_vehicle_charge_state",
        translation_key="active_vehicle_charge_state",
        device_class=SensorDeviceClass.ENUM,
        options=list(CHARGE_STATE_CLASSES),
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.vehicle_charge_state,
    ),
    EvChargingSensorDescription(
        key="active_vehicle_charge_end",
        translation_key="active_vehicle_charge_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.vehicle_charge_end,
    ),
    EvChargingSensorDescription(
        key="session_soc_start",
        translation_key="session_soc_start",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.soc_start,
    ),
    EvChargingSensorDescription(
        key="session_odometer_start",
        translation_key="session_odometer_start",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.odometer_start,
    ),
    EvChargingSensorDescription(
        key="session_duration_net",
        translation_key="session_duration_net",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.duration_net_min,
    ),
    EvChargingSensorDescription(
        key="grid_share",
        translation_key="grid_share",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.grid_share_pct,
    ),
)


@dataclass(frozen=True, kw_only=True)
class EvChargingVehicleSensorDescription(SensorEntityDescription):
    """A sensor and the way its value is taken from a vehicle's own published snapshot."""

    value_fn: Callable[[VehicleSnapshot], StateType | datetime]


VEHICLE_SENSORS: tuple[EvChargingVehicleSensorDescription, ...] = (
    EvChargingVehicleSensorDescription(
        key="session_state",
        translation_key="vehicle_session_state",
        device_class=SensorDeviceClass.ENUM,
        options=list(SESSION_STATES),
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.session_state,
    ),
    EvChargingVehicleSensorDescription(
        key="session_location",
        translation_key="vehicle_session_location",
        device_class=SensorDeviceClass.ENUM,
        options=list(LOCATIONS),
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.session_location,
    ),
    EvChargingVehicleSensorDescription(
        key="session_soc_start",
        translation_key="vehicle_session_soc_start",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.session_soc_start,
    ),
    EvChargingVehicleSensorDescription(
        key="session_odometer_start",
        translation_key="vehicle_session_odometer_start",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.session_odometer_start,
    ),
    EvChargingVehicleSensorDescription(
        key="session_duration_net",
        translation_key="vehicle_session_duration_net",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.session_duration_net_min,
    ),
    EvChargingVehicleSensorDescription(
        key="charge_end",
        translation_key="vehicle_charge_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.charge_end,
    ),
)

# Only offered when the vehicle has a soc or energy_session role, per 11.5.
VEHICLE_SESSION_ENERGY = EvChargingVehicleSensorDescription(
    key="session_energy",
    translation_key="vehicle_session_energy",
    device_class=SensorDeviceClass.ENERGY,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    suggested_display_precision=3,
    entity_registry_enabled_default=False,
    value_fn=lambda snapshot: snapshot.session_energy_kwh,
)


class EvChargingEntity(Entity):
    """Shared behavior of the entities: read the snapshot and follow the manager.

    The entities belong to the subentry of the wallbox and have no device. Their
    names start with the name of the wallbox.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: SessionManager, entry_id: str, key: str) -> None:
        """Bind the entity to the manager."""
        self._manager = manager
        assert manager.wallbox is not None
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_translation_placeholders = {"wallbox": manager.wallbox.name}

    async def async_added_to_hass(self) -> None:
        """Follow published snapshots for as long as the entity exists."""
        self.async_on_remove(self._manager.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        """Write the new state."""
        self.async_write_ha_state()


class EvChargingSensor(EvChargingEntity, SensorEntity):
    """A sensor that shows a value of the published snapshot."""

    entity_description: EvChargingSensorDescription

    def __init__(
        self,
        manager: SessionManager,
        entry_id: str,
        description: EvChargingSensorDescription,
        currency: str,
    ) -> None:
        """Create the sensor."""
        super().__init__(manager, entry_id, description.key)
        self.entity_description = description
        if description.per_currency:
            unit = f"{currency}/{UnitOfEnergy.KILO_WATT_HOUR}" if description.per_kwh else currency
            self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> StateType | datetime:
        """Return the value from the current snapshot."""
        return self.entity_description.value_fn(self._manager.snapshot)

    @property
    def last_reset(self) -> datetime | None:
        """Return the session start for the cost, which begins from zero with each session."""
        if self.entity_description.key == "session_cost":
            return self._manager.snapshot.session_start
        return None


class EvChargingVehicleEntity(Entity):
    """Shared behavior of a vehicle's own entities: read its snapshot, follow the manager.

    The entities belong to the vehicle's own subentry and have no device.
    Their names start with the name of the vehicle.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: SessionManager, context: VehicleContext, key: str) -> None:
        """Bind the entity to the manager and the vehicle it reports on."""
        self._manager = manager
        self._vehicle_id = context.vehicle.id
        self._attr_unique_id = f"{context.subentry_id}_{key}"
        self._attr_translation_placeholders = {"vehicle": context.vehicle.name}

    async def async_added_to_hass(self) -> None:
        """Follow published snapshots for as long as the entity exists."""
        self.async_on_remove(self._manager.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        """Write the new state."""
        self.async_write_ha_state()

    @property
    def _snapshot(self) -> VehicleSnapshot | None:
        """Return this vehicle's current snapshot, if the manager published one yet."""
        return self._manager.vehicle_snapshots.get(self._vehicle_id)


class EvChargingVehicleSensor(EvChargingVehicleEntity, SensorEntity):
    """A sensor that shows a value of a vehicle's own published snapshot."""

    entity_description: EvChargingVehicleSensorDescription

    def __init__(
        self,
        manager: SessionManager,
        context: VehicleContext,
        description: EvChargingVehicleSensorDescription,
    ) -> None:
        """Create the sensor."""
        super().__init__(manager, context, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType | datetime:
        """Return the value from the vehicle's current snapshot."""
        snapshot = self._snapshot
        return self.entity_description.value_fn(snapshot) if snapshot is not None else None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EvChargingConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors of the session capture."""
    manager = entry.runtime_data.manager
    if manager is None:
        return
    async_add_entities(
        (
            EvChargingSensor(manager, entry.entry_id, description, hass.config.currency)
            for description in SENSORS
        ),
        config_subentry_id=manager.wallbox_subentry_id,
    )
    for context in manager.vehicle_contexts:
        if not context.vehicle.active or context.vehicle.is_guest:
            continue
        descriptions = list(VEHICLE_SENSORS)
        if context.vehicle.soc is not None or context.vehicle.energy_session is not None:
            descriptions.append(VEHICLE_SESSION_ENERGY)
        async_add_entities(
            (
                EvChargingVehicleSensor(manager, context, description)
                for description in descriptions
            ),
            config_subentry_id=context.subentry_id,
        )
