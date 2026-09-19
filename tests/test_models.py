"""Tests for the ev_charging data models."""

from dataclasses import FrozenInstanceError

import pytest
from custom_components.ev_charging.models import (
    Card,
    HubSettings,
    Phase,
    Session,
    Vehicle,
    Wallbox,
    derive_energy_kwh,
    merge_shortest_pauses,
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
        manufacturer="KEBA",
        model="P40",
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
    assert wallbox.manufacturer is None
    assert wallbox.model is None
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


def test_phase_round_trips_through_dict() -> None:
    """A phase survives a to_dict/from_dict round trip unchanged."""
    phase = Phase(
        start="2026-09-05T18:12:04+02:00",
        end="2026-09-05T20:00:00+02:00",
        duration_min=108.0,
        energy_kwh=12.5,
        energy_grid_kwh=3.0,
        energy_solar_kwh=9.5,
        cost=0.9,
        power_avg_kw=6.9,
        power_max_kw=11.0,
    )
    assert Phase.from_dict(phase.to_dict()) == phase


def test_phase_from_dict_defaults_optional_fields_to_none() -> None:
    """A phase with only a start, as with an external session, loads with null fields."""
    phase = Phase.from_dict({"start": "2026-09-05T18:12:04+02:00"})
    assert phase.end is None
    assert phase.energy_kwh is None
    assert phase.power_max_kw is None


def test_phase_is_frozen() -> None:
    """A phase cannot be mutated after creation."""
    phase = Phase(start="2026-09-05T18:12:04+02:00")
    with pytest.raises(FrozenInstanceError):
        phase.end = "2026-09-05T20:00:00+02:00"  # type: ignore[misc]


def test_session_round_trips_through_dict_with_phases() -> None:
    """A session including its phases survives a to_dict/from_dict round trip."""
    session = Session(
        id="2026-09-05T18:12:04_v002",
        location="home",
        plug_start="2026-09-05T18:12:04+02:00",
        identification_source="rfid",
        vehicle_id="v002",
        vehicle_name="GLB 250+ EQ",
        capacity_kwh=85.0,
        wallbox_id="wb001",
        card_uid="BAEB2194",
        card_label="Karte GLB",
        plug_end="2026-09-07T09:40:11+02:00",
        plug_duration_min=2608.0,
        charge_duration_min=412.0,
        pause_duration_min=2196.0,
        phase_count=1,
        phases_recorded=True,
        soc_start=42.0,
        soc_end=100.0,
        odometer_km=7699.0,
        energy_measured_kwh=48.213,
        energy_measured_session_kwh=48.207,
        energy_raw_kwh=49.30,
        energy_kwh=48.213,
        energy_grid_kwh=12.104,
        energy_solar_kwh=36.109,
        cost=4.87,
        charge_type="ac",
        charge_type_source="wallbox_config",
        power_avg_kw=7.02,
        status="complete",
        open_fields=("soc_end",),
        modified_fields=("energy_billed_kwh",),
        phases=(Phase(start="2026-09-05T18:12:04+02:00", end="2026-09-07T09:40:11+02:00"),),
    )
    assert Session.from_dict(session.to_dict()) == session


def test_session_from_dict_applies_defaults_for_missing_optional_fields() -> None:
    """Loading a sparse dict, as an unassigned session, yields sensible defaults."""
    session = Session.from_dict(
        {
            "id": "2026-09-05T18:12:04_wb001",
            "location": "home",
            "plug_start": "2026-09-05T18:12:04+02:00",
            "identification_source": "unresolved",
        }
    )
    assert session.vehicle_id is None
    assert session.identification_conflict is False
    assert session.charge_type == "unknown"
    assert session.status == "complete"
    assert session.open_fields == ()
    assert session.phases == ()


def test_session_is_frozen() -> None:
    """A session cannot be mutated after creation."""
    session = Session(
        id="2026-09-05T18:12:04_v002",
        location="home",
        plug_start="2026-09-05T18:12:04+02:00",
        identification_source="rfid",
    )
    with pytest.raises(FrozenInstanceError):
        session.status = "flagged"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"energy_kwh": 5.0, "energy_estimated_kwh": 5.0}, True),
        ({"energy_kwh": 5.0, "energy_measured_kwh": 5.0}, False),
        ({"energy_kwh": 5.0, "energy_billed_kwh": 5.0, "energy_estimated_kwh": 6.0}, False),
        ({"energy_kwh": 5.0, "energy_vehicle_kwh": 5.0}, False),
        ({"energy_kwh": None}, False),
    ],
)
def test_session_energy_is_an_estimate_only_without_a_higher_ranked_source(
    fields: dict, expected: bool
) -> None:
    """energy_kwh counts as estimated when billed, measured and vehicle energy are all absent."""
    session = Session(
        id="a",
        location="home",
        plug_start="2026-09-05T18:12:04+02:00",
        identification_source="manual",
        **fields,
    )
    assert session.energy_is_estimate is expected


def test_derived_energy_takes_the_first_available_source_in_order() -> None:
    """Billed, then measured, then vehicle, then estimated energy."""
    assert derive_energy_kwh(9.0, 8.0, 7.0, 6.0) == 9.0
    assert derive_energy_kwh(None, 8.0, 7.0, 6.0) == 8.0
    assert derive_energy_kwh(None, None, 7.0, 6.0) == 7.0
    assert derive_energy_kwh(None, None, None, 6.0) == 6.0
    assert derive_energy_kwh(None, None, None, None) is None


def _phase(start: str, end: str, energy: float) -> Phase:
    return Phase(start=start, end=end, duration_min=None, energy_kwh=energy, power_max_kw=energy)


def test_merge_shortest_pauses_joins_across_the_shortest_gap() -> None:
    """Three phases reduced to two are joined where the pause between them is shortest."""
    phases = (
        _phase("2026-09-05T10:00:00+02:00", "2026-09-05T10:30:00+02:00", 1.0),
        _phase("2026-09-05T11:00:00+02:00", "2026-09-05T11:30:00+02:00", 2.0),
        _phase("2026-09-05T11:40:00+02:00", "2026-09-05T12:00:00+02:00", 4.0),
    )

    merged = merge_shortest_pauses(phases, 2)

    assert len(merged) == 2
    assert merged[0] == phases[0]
    assert merged[1].start == "2026-09-05T11:00:00+02:00"
    assert merged[1].end == "2026-09-05T12:00:00+02:00"
    assert merged[1].energy_kwh == 6.0
    assert merged[1].power_max_kw == 4.0
    assert merged[1].duration_min == 60.0


def test_merge_shortest_pauses_leaves_a_short_list_alone() -> None:
    """A list within the limit is returned unchanged."""
    phases = (_phase("2026-09-05T10:00:00+02:00", "2026-09-05T10:30:00+02:00", 1.0),)

    assert merge_shortest_pauses(phases, 200) == phases
