"""Tests for the ev_charging data models."""

from dataclasses import FrozenInstanceError

import pytest
from custom_components.ev_charging.models import (
    Card,
    HubSettings,
    Vehicle,
    Wallbox,
    normalize_card_uid,
)


def test_normalize_card_uid_strips_separators_and_upcases() -> None:
    """A card uid is normalized regardless of the source formatting."""
    assert normalize_card_uid("de-abc-c12345678-9") == "DEABCC123456789"
    assert normalize_card_uid("DEABCC123456789") == "DEABCC123456789"
    assert normalize_card_uid("ab cd: ef") == "ABCDEF"


def test_card_round_trips_through_dict() -> None:
    """A card survives a to_dict/from_dict round trip unchanged."""
    card = Card(uid="ABC123", label="Karte GLB", type="rfid", active=True)
    assert Card.from_dict(card.to_dict()) == card


def test_card_from_dict_defaults_type_to_rfid() -> None:
    """A card dict without a type field is treated as an rfid card."""
    card = Card.from_dict({"uid": "ABC123", "label": "Karte GLB", "active": True})
    assert card.type == "rfid"


def test_card_is_frozen() -> None:
    """A card cannot be mutated after creation."""
    card = Card(uid="ABC123", label="Karte GLB")
    with pytest.raises(FrozenInstanceError):
        card.label = "Andere Karte"  # type: ignore[misc]


def test_wallbox_round_trips_through_dict() -> None:
    """A wallbox survives a to_dict/from_dict round trip unchanged."""
    wallbox = Wallbox(
        id="wb001",
        name="Carport",
        current_type="ac",
        max_power_kw=11.0,
    )
    assert Wallbox.from_dict(wallbox.to_dict()) == wallbox


def test_wallbox_from_dict_applies_defaults_for_missing_optional_fields() -> None:
    """Loading an older, sparser dict still yields sensible defaults."""
    wallbox = Wallbox.from_dict(
        {
            "id": "wb001",
            "name": "Carport",
            "current_type": "ac",
            "max_power_kw": 11.0,
        }
    )
    assert wallbox.power_threshold_kw == 0.5
    assert wallbox.start_debounce_s == 2
    assert wallbox.identification_window_s == 15


def test_vehicle_round_trips_through_dict_with_cards() -> None:
    """A vehicle including its cards survives a to_dict/from_dict round trip."""
    vehicle = Vehicle(
        id="v001",
        name="GLB 250+ EQ",
        manufacturer="Mercedes-Benz",
        model="GLB 250+ EQ",
        capacity_kwh=85.0,
        cards=(Card(uid="ABC123", label="Karte GLB", type="rfid"),),
    )
    assert Vehicle.from_dict(vehicle.to_dict()) == vehicle


def test_vehicle_from_dict_applies_defaults_for_missing_optional_fields() -> None:
    """Loading an older, sparser dict still yields sensible defaults."""
    vehicle = Vehicle.from_dict({"id": "v001", "name": "GLB 250+ EQ", "capacity_kwh": 85.0})
    assert vehicle.manufacturer is None
    assert vehicle.model is None
    assert vehicle.cost_mode == "dynamic"


def test_vehicle_is_frozen() -> None:
    """A vehicle cannot be mutated after creation."""
    vehicle = Vehicle(id="v001", name="GLB 250+ EQ", capacity_kwh=85.0)
    with pytest.raises(FrozenInstanceError):
        vehicle.active = False  # type: ignore[misc]


def test_hub_settings_round_trips_through_dict() -> None:
    """Hub settings survive a to_dict/from_dict round trip unchanged."""
    settings = HubSettings(
        update_interval_s=60,
        solar_valuation="zero",
        geocoding_enabled=True,
        geocoding_url="https://example.invalid/reverse",
        geocoding_contact="test@example.invalid",
        estimate_uncertain_threshold_pct=10,
    )
    assert HubSettings.from_dict(settings.to_dict()) == settings


def test_hub_settings_from_dict_applies_defaults_for_missing_fields() -> None:
    """Loading an empty dict yields the documented defaults."""
    settings = HubSettings.from_dict({})
    assert settings.update_interval_s == 30
    assert settings.solar_valuation == "feed_in_tariff"
    assert settings.geocoding_enabled is True
    assert settings.geocoding_contact is None
    assert settings.estimate_uncertain_threshold_pct == 5
