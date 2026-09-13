"""Data models for the ev_charging integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import (
    COST_MODE_DYNAMIC,
    DEFAULT_POWER_THRESHOLD_KW,
    DEFAULT_START_DEBOUNCE_S,
    SOLAR_VALUATION_FEED_IN_TARIFF,
)


def normalize_card_uid(uid: str) -> str:
    """Normalize a card identifier to its canonical stored form."""
    normalized = uid.upper()
    for character in (":", "-", " "):
        normalized = normalized.replace(character, "")
    return normalized


@dataclass(frozen=True, slots=True)
class Card:
    """A card or eMAID that can identify a vehicle at the wallbox."""

    uid: str
    label: str
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {"uid": self.uid, "label": self.label, "active": self.active}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Card:
        """Deserialize from a plain dict."""
        return cls(uid=data["uid"], label=data["label"], active=data["active"])


@dataclass(frozen=True, slots=True)
class Wallbox:
    """Master data of the wallbox subentry."""

    id: str
    name: str
    current_type: str
    max_power_kw: float
    power_threshold_kw: float = DEFAULT_POWER_THRESHOLD_KW
    start_debounce_s: int = DEFAULT_START_DEBOUNCE_S
    # Reserved for the entity-roles stage. Not yet exposed in the dialog:
    # meaningless without an identification role to fall back from.
    default_vehicle_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "name": self.name,
            "current_type": self.current_type,
            "max_power_kw": self.max_power_kw,
            "power_threshold_kw": self.power_threshold_kw,
            "start_debounce_s": self.start_debounce_s,
            "default_vehicle_id": self.default_vehicle_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Wallbox:
        """Deserialize from a plain dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            current_type=data["current_type"],
            max_power_kw=data["max_power_kw"],
            power_threshold_kw=data.get("power_threshold_kw", DEFAULT_POWER_THRESHOLD_KW),
            start_debounce_s=data.get("start_debounce_s", DEFAULT_START_DEBOUNCE_S),
            default_vehicle_id=data.get("default_vehicle_id"),
        )


@dataclass(frozen=True, slots=True)
class Vehicle:
    """Master data of the vehicle subentry."""

    id: str
    name: str
    active: bool = True
    is_guest: bool = False
    vin: str | None = None
    capacity_kwh: float | None = None
    cost_mode: str = COST_MODE_DYNAMIC
    static_price: float | None = None
    solar_valuation: str = SOLAR_VALUATION_FEED_IN_TARIFF
    cards: tuple[Card, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "name": self.name,
            "active": self.active,
            "is_guest": self.is_guest,
            "vin": self.vin,
            "capacity_kwh": self.capacity_kwh,
            "cost_mode": self.cost_mode,
            "static_price": self.static_price,
            "solar_valuation": self.solar_valuation,
            "cards": [card.to_dict() for card in self.cards],
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
            capacity_kwh=data.get("capacity_kwh"),
            cost_mode=data.get("cost_mode", COST_MODE_DYNAMIC),
            static_price=data.get("static_price"),
            solar_valuation=data.get("solar_valuation", SOLAR_VALUATION_FEED_IN_TARIFF),
            cards=tuple(Card.from_dict(card) for card in data.get("cards", [])),
        )
