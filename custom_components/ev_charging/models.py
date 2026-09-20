"""Data models for the ev_charging integration."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from .const import (
    CARD_TYPE_RFID,
    CHARGE_TYPE_UNKNOWN,
    COST_MODE_DYNAMIC,
    DEFAULT_DIRECT_READ_PORT,
    DEFAULT_DIRECT_READ_UNIT_ID,
    DEFAULT_ESTIMATE_UNCERTAIN_THRESHOLD_PCT,
    DEFAULT_GEOCODING_ENABLED,
    DEFAULT_GEOCODING_URL,
    DEFAULT_IDENTIFICATION_WINDOW_S,
    DEFAULT_POWER_THRESHOLD_KW,
    DEFAULT_START_DEBOUNCE_S,
    DEFAULT_UPDATE_INTERVAL_S,
    SESSION_STATUS_COMPLETE,
    SOLAR_VALUATION_FEED_IN_TARIFF,
)


def normalize_card_uid(uid: str) -> str:
    """Normalize a card identifier to its canonical stored form."""
    normalized = uid.upper()
    for character in (":", "-", " "):
        normalized = normalized.replace(character, "")
    return normalized


@dataclass(frozen=True, slots=True)
class EntityRole:
    """A resolved entity role (5.1, 5.2, 4.2).

    The registry entry id is the stable reference used to resolve the role at
    runtime (E15). entity_id is kept only as a display fallback and for
    entities without a registry entry. unit is the unit_of_measurement seen
    at assignment time, for roles that carry a numeric value.
    """

    entity_id: str
    registry_entry_id: str | None = None
    unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "entity_id": self.entity_id,
            "registry_entry_id": self.registry_entry_id,
            "unit": self.unit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EntityRole:
        """Deserialize from a plain dict."""
        return cls(
            entity_id=data["entity_id"],
            registry_entry_id=data.get("registry_entry_id"),
            unit=data.get("unit"),
        )


def _role_to_dict(role: EntityRole | None) -> dict[str, Any] | None:
    """Serialize an optional role."""
    return role.to_dict() if role is not None else None


def _role_from_dict(data: dict[str, Any] | None) -> EntityRole | None:
    """Deserialize an optional role."""
    return EntityRole.from_dict(data) if data is not None else None


@dataclass(frozen=True, slots=True)
class Card:
    """A card or eMAID that can identify a vehicle at the wallbox."""

    uid: str
    label: str
    type: str = CARD_TYPE_RFID
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {"uid": self.uid, "label": self.label, "type": self.type, "active": self.active}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Card:
        """Deserialize from a plain dict."""
        return cls(
            uid=data["uid"],
            label=data["label"],
            type=data.get("type", CARD_TYPE_RFID),
            active=data["active"],
        )


@dataclass(frozen=True, slots=True)
class Wallbox:
    """Master data of the wallbox subentry."""

    id: str
    name: str
    current_type: str
    max_power_kw: float
    manufacturer: str | None = None
    model: str | None = None
    power_threshold_kw: float = DEFAULT_POWER_THRESHOLD_KW
    start_debounce_s: int = DEFAULT_START_DEBOUNCE_S
    identification_window_s: int = DEFAULT_IDENTIFICATION_WINDOW_S
    # Read-only access to the wallbox itself. host, port and unit_id are only
    # used while the identification is read from the register.
    host: str | None = None
    port: int = DEFAULT_DIRECT_READ_PORT
    unit_id: int = DEFAULT_DIRECT_READ_UNIT_ID
    # The identification role is read from the device's register, taken from
    # the chosen mapping, instead of from an entity.
    identification_from_register: bool = False
    # id of the chosen mapping file (4.7). Mandatory before a wallbox can be
    # saved, since plug_state can only be classified once a device is chosen.
    mapping_id: str | None = None
    # Entity roles (5.1). charge_power, plug_state and mapping_id are
    # mandatory before a wallbox can be saved; at least one of energy_total
    # and energy_session is mandatory. Enforced by the config flow, not by
    # this dataclass.
    charge_power: EntityRole | None = None
    energy_total: EntityRole | None = None
    energy_session: EntityRole | None = None
    plug_state: EntityRole | None = None
    identification: EntityRole | None = None
    error: EntityRole | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "name": self.name,
            "current_type": self.current_type,
            "max_power_kw": self.max_power_kw,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "power_threshold_kw": self.power_threshold_kw,
            "start_debounce_s": self.start_debounce_s,
            "identification_window_s": self.identification_window_s,
            "host": self.host,
            "port": self.port,
            "unit_id": self.unit_id,
            "identification_from_register": self.identification_from_register,
            "mapping_id": self.mapping_id,
            "charge_power": _role_to_dict(self.charge_power),
            "energy_total": _role_to_dict(self.energy_total),
            "energy_session": _role_to_dict(self.energy_session),
            "plug_state": _role_to_dict(self.plug_state),
            "identification": _role_to_dict(self.identification),
            "error": _role_to_dict(self.error),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Wallbox:
        """Deserialize from a plain dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            current_type=data["current_type"],
            max_power_kw=data["max_power_kw"],
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            power_threshold_kw=data.get("power_threshold_kw", DEFAULT_POWER_THRESHOLD_KW),
            start_debounce_s=data.get("start_debounce_s", DEFAULT_START_DEBOUNCE_S),
            identification_window_s=data.get(
                "identification_window_s", DEFAULT_IDENTIFICATION_WINDOW_S
            ),
            host=data.get("host"),
            port=data.get("port", DEFAULT_DIRECT_READ_PORT),
            unit_id=data.get("unit_id", DEFAULT_DIRECT_READ_UNIT_ID),
            identification_from_register=data.get("identification_from_register", False),
            mapping_id=data.get("mapping_id"),
            charge_power=_role_from_dict(data.get("charge_power")),
            energy_total=_role_from_dict(data.get("energy_total")),
            energy_session=_role_from_dict(data.get("energy_session")),
            plug_state=_role_from_dict(data.get("plug_state")),
            identification=_role_from_dict(data.get("identification")),
            error=_role_from_dict(data.get("error")),
        )


@dataclass(frozen=True, slots=True)
class Vehicle:
    """Master data of the vehicle subentry."""

    id: str
    name: str
    active: bool = True
    is_guest: bool = False
    vin: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    capacity_kwh: float | None = None
    cost_mode: str = COST_MODE_DYNAMIC
    cards: tuple[Card, ...] = field(default_factory=tuple)
    # Identification via the vehicle's own integration (4.4, 7.8). Only
    # selectable when charge_state and location are assigned.
    identify_by_vehicle_api: bool = False
    # id of the chosen mapping file (4.7). Optional: a vehicle without
    # charge_state or charge_type needs no device, for example a guest
    # vehicle or one tracked only via soc/odometer/location. Mandatory as
    # soon as charge_state or charge_type is assigned, enforced by the
    # config flow.
    mapping_id: str | None = None
    # Entity roles (5.2), all optional.
    soc: EntityRole | None = None
    soc_target: EntityRole | None = None
    odometer: EntityRole | None = None
    charge_state: EntityRole | None = None
    charge_type: EntityRole | None = None
    # Vehicle-side connection state (5.2), classified via the chosen mapping
    # like the wallbox's own plug_state. Some vehicle integrations'
    # charge_state never reports a disconnected value of its own; plug_state
    # fills that gap from a separate entity, e.g. a connectivity binary_sensor.
    plug_state: EntityRole | None = None
    energy_session: EntityRole | None = None
    location: EntityRole | None = None
    charge_end: EntityRole | None = None
    charge_power: EntityRole | None = None
    range: EntityRole | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "name": self.name,
            "active": self.active,
            "is_guest": self.is_guest,
            "vin": self.vin,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "capacity_kwh": self.capacity_kwh,
            "cost_mode": self.cost_mode,
            "cards": [card.to_dict() for card in self.cards],
            "identify_by_vehicle_api": self.identify_by_vehicle_api,
            "mapping_id": self.mapping_id,
            "soc": _role_to_dict(self.soc),
            "soc_target": _role_to_dict(self.soc_target),
            "odometer": _role_to_dict(self.odometer),
            "charge_state": _role_to_dict(self.charge_state),
            "charge_type": _role_to_dict(self.charge_type),
            "plug_state": _role_to_dict(self.plug_state),
            "energy_session": _role_to_dict(self.energy_session),
            "location": _role_to_dict(self.location),
            "charge_end": _role_to_dict(self.charge_end),
            "charge_power": _role_to_dict(self.charge_power),
            "range": _role_to_dict(self.range),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Vehicle:
        """Deserialize from a plain dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            active=data.get("active", True),
            is_guest=data.get("is_guest", False),
            vin=data.get("vin"),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            capacity_kwh=data.get("capacity_kwh"),
            cost_mode=data.get("cost_mode", COST_MODE_DYNAMIC),
            cards=tuple(Card.from_dict(card) for card in data.get("cards", [])),
            identify_by_vehicle_api=data.get("identify_by_vehicle_api", False),
            mapping_id=data.get("mapping_id"),
            soc=_role_from_dict(data.get("soc")),
            soc_target=_role_from_dict(data.get("soc_target")),
            odometer=_role_from_dict(data.get("odometer")),
            charge_state=_role_from_dict(data.get("charge_state")),
            charge_type=_role_from_dict(data.get("charge_type")),
            plug_state=_role_from_dict(data.get("plug_state")),
            energy_session=_role_from_dict(data.get("energy_session")),
            location=_role_from_dict(data.get("location")),
            charge_end=_role_from_dict(data.get("charge_end")),
            charge_power=_role_from_dict(data.get("charge_power")),
            range=_role_from_dict(data.get("range")),
        )


@dataclass(frozen=True, slots=True)
class HubSettings:
    """Global settings held on the hub config entry (4.2)."""

    update_interval_s: int = DEFAULT_UPDATE_INTERVAL_S
    solar_valuation: str = SOLAR_VALUATION_FEED_IN_TARIFF
    geocoding_enabled: bool = DEFAULT_GEOCODING_ENABLED
    geocoding_url: str = DEFAULT_GEOCODING_URL
    geocoding_contact: str | None = None
    estimate_uncertain_threshold_pct: float = DEFAULT_ESTIMATE_UNCERTAIN_THRESHOLD_PCT
    # Grid balance and price roles. grid_power is an alternative to the pair
    # grid_import/grid_export; without either, no split into grid and solar
    # share is made. price_grid and price_feed_in each accept either an
    # entity role or a fixed value, never both.
    grid_power: EntityRole | None = None
    grid_power_inverted: bool = False
    grid_import: EntityRole | None = None
    grid_export: EntityRole | None = None
    price_grid: EntityRole | None = None
    price_grid_fixed: float | None = None
    price_feed_in: EntityRole | None = None
    price_feed_in_fixed: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "update_interval_s": self.update_interval_s,
            "solar_valuation": self.solar_valuation,
            "geocoding_enabled": self.geocoding_enabled,
            "geocoding_url": self.geocoding_url,
            "geocoding_contact": self.geocoding_contact,
            "estimate_uncertain_threshold_pct": self.estimate_uncertain_threshold_pct,
            "grid_power": _role_to_dict(self.grid_power),
            "grid_power_inverted": self.grid_power_inverted,
            "grid_import": _role_to_dict(self.grid_import),
            "grid_export": _role_to_dict(self.grid_export),
            "price_grid": _role_to_dict(self.price_grid),
            "price_grid_fixed": self.price_grid_fixed,
            "price_feed_in": _role_to_dict(self.price_feed_in),
            "price_feed_in_fixed": self.price_feed_in_fixed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HubSettings:
        """Deserialize from a plain dict, defaulting fields that are missing."""
        return cls(
            update_interval_s=data.get("update_interval_s", DEFAULT_UPDATE_INTERVAL_S),
            solar_valuation=data.get("solar_valuation", SOLAR_VALUATION_FEED_IN_TARIFF),
            geocoding_enabled=data.get("geocoding_enabled", DEFAULT_GEOCODING_ENABLED),
            geocoding_url=data.get("geocoding_url", DEFAULT_GEOCODING_URL),
            geocoding_contact=data.get("geocoding_contact"),
            estimate_uncertain_threshold_pct=data.get(
                "estimate_uncertain_threshold_pct", DEFAULT_ESTIMATE_UNCERTAIN_THRESHOLD_PCT
            ),
            grid_power=_role_from_dict(data.get("grid_power")),
            grid_power_inverted=data.get("grid_power_inverted", False),
            grid_import=_role_from_dict(data.get("grid_import")),
            grid_export=_role_from_dict(data.get("grid_export")),
            price_grid=_role_from_dict(data.get("price_grid")),
            price_grid_fixed=data.get("price_grid_fixed"),
            price_feed_in=_role_from_dict(data.get("price_feed_in")),
            price_feed_in_fixed=data.get("price_feed_in_fixed"),
        )


@dataclass(frozen=True, slots=True)
class Phase:
    """A single charging phase within a session (6.3).

    An external session without a wallbox counter carries only the time
    range; the energy, cost and power fields stay null.
    """

    start: str
    end: str | None = None
    duration_min: float | None = None
    energy_kwh: float | None = None
    energy_grid_kwh: float | None = None
    energy_solar_kwh: float | None = None
    cost: float | None = None
    power_avg_kw: float | None = None
    power_max_kw: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "start": self.start,
            "end": self.end,
            "duration_min": self.duration_min,
            "energy_kwh": self.energy_kwh,
            "energy_grid_kwh": self.energy_grid_kwh,
            "energy_solar_kwh": self.energy_solar_kwh,
            "cost": self.cost,
            "power_avg_kw": self.power_avg_kw,
            "power_max_kw": self.power_max_kw,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Phase:
        """Deserialize from a plain dict."""
        return cls(
            start=data["start"],
            end=data.get("end"),
            duration_min=data.get("duration_min"),
            energy_kwh=data.get("energy_kwh"),
            energy_grid_kwh=data.get("energy_grid_kwh"),
            energy_solar_kwh=data.get("energy_solar_kwh"),
            cost=data.get("cost"),
            power_avg_kw=data.get("power_avg_kw"),
            power_max_kw=data.get("power_max_kw"),
        )


@dataclass(frozen=True, slots=True)
class Session:
    """A single charging session (6.2).

    vehicle_id stays null for as long as a session is not assigned to a
    vehicle (7.8). energy_measured_kwh, energy_measured_session_kwh,
    energy_vehicle_kwh, energy_raw_kwh and energy_billed_kwh are each
    written by at most one source and never overwritten; energy_kwh is
    always derived from them (8.4). cost carries only the dynamically
    determined amount; there is no fixed-price field.
    """

    id: str
    location: str
    plug_start: str
    identification_source: str

    vehicle_id: str | None = None
    vehicle_name: str | None = None
    capacity_kwh: float | None = None
    wallbox_id: str | None = None
    card_uid: str | None = None
    card_label: str | None = None
    identification_conflict: bool = False

    plug_end: str | None = None
    plug_duration_min: float | None = None
    charge_duration_min: float | None = None
    pause_duration_min: float | None = None
    phase_count: int = 0
    phases_recorded: bool = True

    soc_start: float | None = None
    soc_end: float | None = None
    odometer_km: float | None = None

    energy_measured_kwh: float | None = None
    energy_measured_session_kwh: float | None = None
    energy_vehicle_kwh: float | None = None
    energy_raw_kwh: float | None = None
    energy_estimated_kwh: float | None = None
    energy_billed_kwh: float | None = None
    energy_kwh: float | None = None
    energy_grid_kwh: float | None = None
    energy_solar_kwh: float | None = None
    energy_unallocated_kwh: float = 0.0
    estimate_uncertain: bool = False

    cost: float | None = None
    charge_type: str = CHARGE_TYPE_UNKNOWN
    charge_type_source: str | None = None
    power_avg_kw: float | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_reported_at: str | None = None
    location_conflict: bool = False
    address_retry_pending: bool = False
    provider: str | None = None
    note: str | None = None

    charge_error: bool = False
    status: str = SESSION_STATUS_COMPLETE
    open_fields: tuple[str, ...] = field(default_factory=tuple)
    created_at: str | None = None
    modified_at: str | None = None
    modified_fields: tuple[str, ...] = field(default_factory=tuple)
    phases: tuple[Phase, ...] = field(default_factory=tuple)

    @property
    def energy_is_estimate(self) -> bool:
        """Whether energy_kwh is only estimated from the state of charge.

        energy_kwh takes the first available of billed, measured, vehicle and
        estimated energy, so it is an estimate exactly when none of the
        three preceding sources is present.
        """
        return (
            self.energy_kwh is not None
            and self.energy_billed_kwh is None
            and self.energy_measured_kwh is None
            and self.energy_vehicle_kwh is None
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "vehicle_name": self.vehicle_name,
            "capacity_kwh": self.capacity_kwh,
            "wallbox_id": self.wallbox_id,
            "card_uid": self.card_uid,
            "card_label": self.card_label,
            "location": self.location,
            "identification_source": self.identification_source,
            "identification_conflict": self.identification_conflict,
            "plug_start": self.plug_start,
            "plug_end": self.plug_end,
            "plug_duration_min": self.plug_duration_min,
            "charge_duration_min": self.charge_duration_min,
            "pause_duration_min": self.pause_duration_min,
            "phase_count": self.phase_count,
            "phases_recorded": self.phases_recorded,
            "soc_start": self.soc_start,
            "soc_end": self.soc_end,
            "odometer_km": self.odometer_km,
            "energy_measured_kwh": self.energy_measured_kwh,
            "energy_measured_session_kwh": self.energy_measured_session_kwh,
            "energy_vehicle_kwh": self.energy_vehicle_kwh,
            "energy_raw_kwh": self.energy_raw_kwh,
            "energy_estimated_kwh": self.energy_estimated_kwh,
            "energy_billed_kwh": self.energy_billed_kwh,
            "energy_kwh": self.energy_kwh,
            "energy_grid_kwh": self.energy_grid_kwh,
            "energy_solar_kwh": self.energy_solar_kwh,
            "energy_unallocated_kwh": self.energy_unallocated_kwh,
            "estimate_uncertain": self.estimate_uncertain,
            "cost": self.cost,
            "charge_type": self.charge_type,
            "charge_type_source": self.charge_type_source,
            "power_avg_kw": self.power_avg_kw,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_reported_at": self.location_reported_at,
            "location_conflict": self.location_conflict,
            "address_retry_pending": self.address_retry_pending,
            "provider": self.provider,
            "note": self.note,
            "charge_error": self.charge_error,
            "status": self.status,
            "open_fields": list(self.open_fields),
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "modified_fields": list(self.modified_fields),
            "phases": [phase.to_dict() for phase in self.phases],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        """Deserialize from a plain dict."""
        return cls(
            id=data["id"],
            vehicle_id=data.get("vehicle_id"),
            vehicle_name=data.get("vehicle_name"),
            capacity_kwh=data.get("capacity_kwh"),
            wallbox_id=data.get("wallbox_id"),
            card_uid=data.get("card_uid"),
            card_label=data.get("card_label"),
            location=data["location"],
            identification_source=data["identification_source"],
            identification_conflict=data.get("identification_conflict", False),
            plug_start=data["plug_start"],
            plug_end=data.get("plug_end"),
            plug_duration_min=data.get("plug_duration_min"),
            charge_duration_min=data.get("charge_duration_min"),
            pause_duration_min=data.get("pause_duration_min"),
            phase_count=data.get("phase_count", 0),
            phases_recorded=data.get("phases_recorded", True),
            soc_start=data.get("soc_start"),
            soc_end=data.get("soc_end"),
            odometer_km=data.get("odometer_km"),
            energy_measured_kwh=data.get("energy_measured_kwh"),
            energy_measured_session_kwh=data.get("energy_measured_session_kwh"),
            energy_vehicle_kwh=data.get("energy_vehicle_kwh"),
            energy_raw_kwh=data.get("energy_raw_kwh"),
            energy_estimated_kwh=data.get("energy_estimated_kwh"),
            energy_billed_kwh=data.get("energy_billed_kwh"),
            energy_kwh=data.get("energy_kwh"),
            energy_grid_kwh=data.get("energy_grid_kwh"),
            energy_solar_kwh=data.get("energy_solar_kwh"),
            energy_unallocated_kwh=data.get("energy_unallocated_kwh", 0.0),
            estimate_uncertain=data.get("estimate_uncertain", False),
            cost=data.get("cost"),
            charge_type=data.get("charge_type", CHARGE_TYPE_UNKNOWN),
            charge_type_source=data.get("charge_type_source"),
            power_avg_kw=data.get("power_avg_kw"),
            address=data.get("address"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            location_reported_at=data.get("location_reported_at"),
            location_conflict=data.get("location_conflict", False),
            address_retry_pending=data.get("address_retry_pending", False),
            provider=data.get("provider"),
            note=data.get("note"),
            charge_error=data.get("charge_error", False),
            status=data.get("status", SESSION_STATUS_COMPLETE),
            open_fields=tuple(data.get("open_fields", [])),
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
            modified_fields=tuple(data.get("modified_fields", [])),
            phases=tuple(Phase.from_dict(phase) for phase in data.get("phases", [])),
        )


def derive_energy_kwh(
    billed: float | None, measured: float | None, vehicle: float | None, estimated: float | None
) -> float | None:
    """Return the authoritative energy of a session.

    The first available of billed, measured, vehicle-reported and estimated
    energy. None of the source fields is ever changed.
    """
    for value in (billed, measured, vehicle, estimated):
        if value is not None:
            return value
    return None


def _sum_optional(first: float | None, second: float | None) -> float | None:
    """Add two optional values; a missing side contributes nothing."""
    if first is None:
        return second
    if second is None:
        return first
    return first + second


def _merge_phase_pair(first: Phase, second: Phase) -> Phase:
    """Join two consecutive phases into one that spans both and the pause between."""
    first_start = datetime.fromisoformat(first.start)
    end = second.end or second.start
    duration = (datetime.fromisoformat(end) - first_start).total_seconds() / 60
    energy = _sum_optional(first.energy_kwh, second.energy_kwh)
    power_max = max(
        (value for value in (first.power_max_kw, second.power_max_kw) if value is not None),
        default=None,
    )
    return replace(
        first,
        end=end,
        duration_min=duration,
        energy_kwh=energy,
        energy_grid_kwh=_sum_optional(first.energy_grid_kwh, second.energy_grid_kwh),
        energy_solar_kwh=_sum_optional(first.energy_solar_kwh, second.energy_solar_kwh),
        cost=_sum_optional(first.cost, second.cost),
        power_avg_kw=energy / (duration / 60) if energy is not None and duration > 0 else None,
        power_max_kw=power_max,
    )


def merge_shortest_pauses(phases: tuple[Phase, ...], limit: int) -> tuple[Phase, ...]:
    """Reduce the phases to at most limit by joining across the shortest pauses.

    All phases must be closed. Returns the phases unchanged when they already fit.
    """
    merged = list(phases)
    while len(merged) > max(limit, 1):
        gaps = [
            (
                datetime.fromisoformat(merged[index + 1].start)
                - datetime.fromisoformat(merged[index].end or merged[index].start)
            ).total_seconds()
            for index in range(len(merged) - 1)
        ]
        index = gaps.index(min(gaps))
        merged[index : index + 2] = [_merge_phase_pair(merged[index], merged[index + 1])]
    return tuple(merged)
