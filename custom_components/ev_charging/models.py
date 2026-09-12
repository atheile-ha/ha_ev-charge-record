"""Data models for the ev_charging integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import (
    DEFAULT_ERROR_DEBOUNCE_S,
    DEFAULT_FINAL_VALUES_GRACE_MIN,
    DEFAULT_IDENTIFICATION_MAX_AGE_MIN,
    DEFAULT_MIN_PAUSE_MIN,
    DEFAULT_POWER_THRESHOLD_KW,
    DEFAULT_SESSION_STALE_H,
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
    session_strategy: str
    power_threshold_kw: float = DEFAULT_POWER_THRESHOLD_KW
    start_debounce_s: int = DEFAULT_START_DEBOUNCE_S
    min_pause_min: int = DEFAULT_MIN_PAUSE_MIN
    session_end_pause_min: int | None = None
    final_values_grace_min: int = DEFAULT_FINAL_VALUES_GRACE_MIN
    identification_max_age_min: int = DEFAULT_IDENTIFICATION_MAX_AGE_MIN
    default_vehicle_id: str | None = None
    error_debounce_s: int = DEFAULT_ERROR_DEBOUNCE_S
    session_stale_h: int = DEFAULT_SESSION_STALE_H

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "name": self.name,
            "current_type": self.current_type,
            "max_power_kw": self.max_power_kw,
            "session_strategy": self.session_strategy,
            "power_threshold_kw": self.power_threshold_kw,
            "start_debounce_s": self.start_debounce_s,
            "min_pause_min": self.min_pause_min,
            "session_end_pause_min": self.session_end_pause_min,
            "final_values_grace_min": self.final_values_grace_min,
            "identification_max_age_min": self.identification_max_age_min,
            "default_vehicle_id": self.default_vehicle_id,
            "error_debounce_s": self.error_debounce_s,
            "session_stale_h": self.session_stale_h,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Wallbox:
        """Deserialize from a plain dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            current_type=data["current_type"],
            max_power_kw=data["max_power_kw"],
            session_strategy=data["session_strategy"],
            power_threshold_kw=data.get("power_threshold_kw", DEFAULT_POWER_THRESHOLD_KW),
            start_debounce_s=data.get("start_debounce_s", DEFAULT_START_DEBOUNCE_S),
            min_pause_min=data.get("min_pause_min", DEFAULT_MIN_PAUSE_MIN),
            session_end_pause_min=data.get("session_end_pause_min"),
            final_values_grace_min=data.get(
                "final_values_grace_min", DEFAULT_FINAL_VALUES_GRACE_MIN
            ),
            identification_max_age_min=data.get(
                "identification_max_age_min", DEFAULT_IDENTIFICATION_MAX_AGE_MIN
            ),
            default_vehicle_id=data.get("default_vehicle_id"),
            error_debounce_s=data.get("error_debounce_s", DEFAULT_ERROR_DEBOUNCE_S),
            session_stale_h=data.get("session_stale_h", DEFAULT_SESSION_STALE_H),
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
    solar_valuation: str = SOLAR_VALUATION_FEED_IN_TARIFF
    solar_valuation_fixed: float | None = None
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
            "solar_valuation": self.solar_valuation,
            "solar_valuation_fixed": self.solar_valuation_fixed,
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
            solar_valuation=data.get("solar_valuation", SOLAR_VALUATION_FEED_IN_TARIFF),
            solar_valuation_fixed=data.get("solar_valuation_fixed"),
            cards=tuple(Card.from_dict(card) for card in data.get("cards", [])),
        )
