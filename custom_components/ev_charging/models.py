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
    power_threshold_kw: float = DEFAULT_POWER_THRESHOLD_KW
    start_debounce_s: int = DEFAULT_START_DEBOUNCE_S
    identification_window_s: int = DEFAULT_IDENTIFICATION_WINDOW_S

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "name": self.name,
            "current_type": self.current_type,
            "max_power_kw": self.max_power_kw,
            "power_threshold_kw": self.power_threshold_kw,
            "start_debounce_s": self.start_debounce_s,
            "identification_window_s": self.identification_window_s,
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
            identification_window_s=data.get(
                "identification_window_s", DEFAULT_IDENTIFICATION_WINDOW_S
            ),
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
        )


@dataclass(frozen=True, slots=True)
class HubSettings:
    """Global settings held on the hub config entry (4.2).

    Only the fields without an entity selector are covered here.
    """

    update_interval_s: int = DEFAULT_UPDATE_INTERVAL_S
    solar_valuation: str = SOLAR_VALUATION_FEED_IN_TARIFF
    geocoding_enabled: bool = DEFAULT_GEOCODING_ENABLED
    geocoding_url: str = DEFAULT_GEOCODING_URL
    geocoding_contact: str | None = None
    estimate_uncertain_threshold_pct: float = DEFAULT_ESTIMATE_UNCERTAIN_THRESHOLD_PCT

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "update_interval_s": self.update_interval_s,
            "solar_valuation": self.solar_valuation,
            "geocoding_enabled": self.geocoding_enabled,
            "geocoding_url": self.geocoding_url,
            "geocoding_contact": self.geocoding_contact,
            "estimate_uncertain_threshold_pct": self.estimate_uncertain_threshold_pct,
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
        )
