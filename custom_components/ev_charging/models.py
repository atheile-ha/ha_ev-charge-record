"""Data models for the ev_charging integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import (
    CARD_TYPE_RFID,
    COST_MODE_DYNAMIC,
    DEFAULT_ESTIMATE_UNCERTAIN_THRESHOLD_PCT,
    DEFAULT_GEOCODING_ENABLED,
    DEFAULT_GEOCODING_URL,
    DEFAULT_IDENTIFICATION_WINDOW_S,
    DEFAULT_POWER_THRESHOLD_KW,
    DEFAULT_START_DEBOUNCE_S,
    DEFAULT_UPDATE_INTERVAL_S,
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
    # Entity roles (5.1). charge_power and plug_state are mandatory before a
    # wallbox can be saved; at least one of energy_total and energy_session
    # is mandatory. Enforced by the config flow, not by this dataclass.
    charge_power: EntityRole | None = None
    energy_total: EntityRole | None = None
    energy_session: EntityRole | None = None
    plug_state: EntityRole | None = None
    plug_state_mapping: dict[str, str] = field(default_factory=dict)
    identification: EntityRole | None = None
    error: EntityRole | None = None
    # Populated only when error is a state entity mapped like plug_state
    # (E29). Left empty when error is a binary_sensor with device_class
    # problem, which is read directly without a mapping.
    error_mapping: dict[str, str] = field(default_factory=dict)

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
            "charge_power": _role_to_dict(self.charge_power),
            "energy_total": _role_to_dict(self.energy_total),
            "energy_session": _role_to_dict(self.energy_session),
            "plug_state": _role_to_dict(self.plug_state),
            "plug_state_mapping": dict(self.plug_state_mapping),
            "identification": _role_to_dict(self.identification),
            "error": _role_to_dict(self.error),
            "error_mapping": dict(self.error_mapping),
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
            charge_power=_role_from_dict(data.get("charge_power")),
            energy_total=_role_from_dict(data.get("energy_total")),
            energy_session=_role_from_dict(data.get("energy_session")),
            plug_state=_role_from_dict(data.get("plug_state")),
            plug_state_mapping=dict(data.get("plug_state_mapping", {})),
            identification=_role_from_dict(data.get("identification")),
            error=_role_from_dict(data.get("error")),
            error_mapping=dict(data.get("error_mapping", {})),
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
    # Entity roles (5.2), all optional.
    soc: EntityRole | None = None
    soc_target: EntityRole | None = None
    odometer: EntityRole | None = None
    charge_state: EntityRole | None = None
    charge_state_mapping: dict[str, str] = field(default_factory=dict)
    charge_type: EntityRole | None = None
    charge_type_mapping: dict[str, str] = field(default_factory=dict)
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
            "soc": _role_to_dict(self.soc),
            "soc_target": _role_to_dict(self.soc_target),
            "odometer": _role_to_dict(self.odometer),
            "charge_state": _role_to_dict(self.charge_state),
            "charge_state_mapping": dict(self.charge_state_mapping),
            "charge_type": _role_to_dict(self.charge_type),
            "charge_type_mapping": dict(self.charge_type_mapping),
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
            soc=_role_from_dict(data.get("soc")),
            soc_target=_role_from_dict(data.get("soc_target")),
            odometer=_role_from_dict(data.get("odometer")),
            charge_state=_role_from_dict(data.get("charge_state")),
            charge_state_mapping=dict(data.get("charge_state_mapping", {})),
            charge_type=_role_from_dict(data.get("charge_type")),
            charge_type_mapping=dict(data.get("charge_type_mapping", {})),
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
