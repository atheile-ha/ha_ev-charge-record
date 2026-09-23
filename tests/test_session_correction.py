"""Tests for update_session, delete_session, close_followup, correct_vehicle and
create_session (7.8, 10, 13, 15), and the recorder lookup they share with the
late vehicle resolution."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest
from custom_components.ev_charging import session_manager
from custom_components.ev_charging.const import (
    DOMAIN,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
    store_key_sessions,
)
from custom_components.ev_charging.models import EntityRole, Phase, Session, Vehicle, Wallbox
from custom_components.ev_charging.store import SessionYearStore
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from tests.test_session_manager import (
    EQB_CHARGE,
    GLB_CHARGE,
    GLB_ODO,
    GLB_SOC,
    _advance,
    _eqb,
    _glb,
    _set,
    _start_charging,
    _stored,
    _unplug,
)
from tests.test_session_manager import (
    _setup as _setup_manager,
)

SESSION_ID = "2026-06-01T10:00:00_v001"


def _mock_history(values: dict[str, tuple[str, str | None]]):
    """Patch recorder history to answer as if each entity's state were recorded.

    values maps an entity_id to (state, unit). Real recorder access is out
    of scope here: this exercises our own use of history.state_changes_during_period
    -- resolving the role, calling it, and normalizing the answer -- without
    depending on a live recorder instance (which conflicts with this
    project's autouse enable_custom_integrations fixture, see 6.1/2.2).
    """

    def _side_effect(
        hass: HomeAssistant, start: Any, end: Any, entity_id: str, **kwargs: Any
    ) -> dict[str, list[State]]:
        found = values.get(entity_id)
        if found is None:
            return {}
        state, unit = found
        attributes = {"unit_of_measurement": unit} if unit else {}
        return {entity_id: [State(entity_id, state, attributes)]}

    return patch(
        "custom_components.ev_charging.session_manager.history.state_changes_during_period",
        side_effect=_side_effect,
    )


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Give this module's hass a private config dir: the year scan reads real files."""
    return hass_tmp_config_dir


def _session(**overrides: Any) -> Session:
    fields: dict[str, Any] = {
        "id": SESSION_ID,
        "location": "home",
        "plug_start": "2026-06-01T10:00:00+02:00",
        "identification_source": "manual",
        "vehicle_id": "v001",
        "vehicle_name": "GLB",
        "capacity_kwh": 85.0,
        "wallbox_id": "wb001",
        "charge_duration_min": 60.0,
        "energy_measured_kwh": 10.0,
        "energy_kwh": 10.0,
        "status": "complete",
    }
    fields.update(overrides)
    return Session(**fields)


async def _touch_year_file(hass: HomeAssistant, year: int) -> None:
    def _touch() -> None:
        storage_dir = hass.config.path(".storage")
        os.makedirs(storage_dir, exist_ok=True)
        open(os.path.join(storage_dir, store_key_sessions(year)), "a", encoding="utf-8").close()

    await hass.async_add_executor_job(_touch)


async def _store_year(hass: HomeAssistant, year: int, sessions: list[Session]) -> None:
    await SessionYearStore(hass, year).async_save(sessions)
    await _touch_year_file(hass, year)


def _add_vehicle(hass: HomeAssistant, vehicle: Vehicle) -> None:
    MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data={},
        subentries_data=[
            {
                "data": vehicle.to_dict(),
                "subentry_type": SUBENTRY_TYPE_VEHICLE,
                "title": vehicle.name,
                "unique_id": None,
            }
        ],
    ).add_to_hass(hass)


def _add_wallbox(hass: HomeAssistant, wallbox: Wallbox) -> None:
    MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data={},
        subentries_data=[
            {
                "data": wallbox.to_dict(),
                "subentry_type": SUBENTRY_TYPE_WALLBOX,
                "title": wallbox.name,
                "unique_id": None,
            }
        ],
    ).add_to_hass(hass)


# ----------------------------------------------------------------- parse_offset_datetime


def test_parse_offset_datetime_rejects_a_naive_timestamp() -> None:
    """6.4: a stored or accepted timestamp always carries a UTC offset."""
    with pytest.raises(ValueError):
        session_manager.parse_offset_datetime("2026-06-01T10:00:00")


def test_parse_offset_datetime_accepts_an_offset() -> None:
    parsed = session_manager.parse_offset_datetime("2026-06-01T10:00:00+02:00")
    assert parsed.tzinfo is not None


# ----------------------------------------------------------------------- update_session


async def test_update_session_rejects_an_unknown_id(hass: HomeAssistant) -> None:
    with pytest.raises(session_manager.SessionNotFoundError):
        await session_manager.async_update_session(hass, "does-not-exist", {"note": "x"})


async def test_update_session_fills_a_missing_field_and_closes_the_followup(
    hass: HomeAssistant,
) -> None:
    """Supplying the only missing field ends the followup without a separate call (10)."""
    await _store_year(
        hass,
        2026,
        [
            _session(
                soc_start=40,
                soc_end=None,
                energy_kwh=None,
                energy_measured_kwh=None,
                open_fields=("soc_end", "energy_kwh"),
                status="followup_open",
            )
        ],
    )

    updated = await session_manager.async_update_session(hass, SESSION_ID, {"soc_end": 80})

    assert updated.soc_end == 80
    assert updated.energy_raw_kwh == pytest.approx(34.0)
    assert updated.energy_kwh == pytest.approx(34.0)
    assert updated.open_fields == ()
    assert updated.status == "complete"
    assert "soc_end" in updated.modified_fields
    (stored,) = await SessionYearStore(hass, 2026).async_load()
    assert stored.soc_end == 80


async def test_update_session_never_touches_the_measured_energy_fields(hass: HomeAssistant) -> None:
    """I2: the measured and vehicle-reported energy fields are never overwritten."""
    await _store_year(
        hass,
        2026,
        [
            _session(
                soc_start=40,
                soc_end=80,
                energy_measured_kwh=33.5,
                energy_measured_session_kwh=33.4,
                energy_vehicle_kwh=None,
                energy_kwh=33.5,
            )
        ],
    )

    updated = await session_manager.async_update_session(
        hass, SESSION_ID, {"soc_end": 90, "energy_billed_kwh": 36.0}
    )

    assert updated.energy_measured_kwh == 33.5
    assert updated.energy_measured_session_kwh == 33.4
    assert updated.energy_vehicle_kwh is None
    assert updated.energy_billed_kwh == 36.0
    assert updated.energy_kwh == pytest.approx(36.0)


async def test_update_session_rejects_charge_type_unless_heuristic(hass: HomeAssistant) -> None:
    """5.5: charge_type is only correctable when it was determined heuristically."""
    await _store_year(hass, 2026, [_session(charge_type="ac", charge_type_source="wallbox_config")])

    with pytest.raises(session_manager.SessionValidationError):
        await session_manager.async_update_session(hass, SESSION_ID, {"charge_type": "dc"})


async def test_update_session_accepts_charge_type_for_a_heuristic_session(
    hass: HomeAssistant,
) -> None:
    await _store_year(hass, 2026, [_session(charge_type="ac", charge_type_source="heuristic")])

    updated = await session_manager.async_update_session(hass, SESSION_ID, {"charge_type": "dc"})

    assert updated.charge_type == "dc"


async def test_update_session_rejects_plug_end_once_it_is_already_set(hass: HomeAssistant) -> None:
    await _store_year(hass, 2026, [_session(plug_end="2026-06-01T12:00:00+02:00")])

    with pytest.raises(session_manager.SessionValidationError):
        await session_manager.async_update_session(
            hass, SESSION_ID, {"plug_end": dt_util.parse_datetime("2026-06-01T13:00:00+02:00")}
        )


async def test_update_session_accepts_plug_end_while_it_is_open(hass: HomeAssistant) -> None:
    """A filled plug_end is stored as an ISO string and its duration is derived."""
    await _store_year(hass, 2026, [_session(plug_end=None)])

    updated = await session_manager.async_update_session(
        hass, SESSION_ID, {"plug_end": dt_util.parse_datetime("2026-06-01T12:00:00+02:00")}
    )

    assert dt_util.parse_datetime(updated.plug_end) == dt_util.parse_datetime(
        "2026-06-01T12:00:00+02:00"
    )
    assert updated.plug_duration_min == pytest.approx(120.0)


async def test_update_session_leaves_a_flagged_status_alone(hass: HomeAssistant) -> None:
    """A session flagged for another reason stays flagged even once complete (12.3)."""
    await _store_year(
        hass,
        2026,
        [_session(status="flagged", open_fields=("cost",), soc_start=40, soc_end=80)],
    )

    updated = await session_manager.async_update_session(hass, SESSION_ID, {"cost": 5.0})

    assert updated.cost == 5.0
    assert updated.open_fields == ()
    assert updated.status == "flagged"


# ----------------------------------------------------------------------- delete_session


async def test_delete_session_rejects_an_unknown_id(hass: HomeAssistant) -> None:
    with pytest.raises(session_manager.SessionNotFoundError):
        await session_manager.async_delete_session(hass, "does-not-exist")


async def test_delete_session_removes_only_the_named_session(hass: HomeAssistant) -> None:
    await _store_year(
        hass, 2026, [_session(id=SESSION_ID), _session(id="2026-07-01T10:00:00_v001")]
    )

    await session_manager.async_delete_session(hass, SESSION_ID)

    remaining = await SessionYearStore(hass, 2026).async_load()
    assert [s.id for s in remaining] == ["2026-07-01T10:00:00_v001"]


# ----------------------------------------------------------------------- close_followup


async def test_close_followup_clears_open_fields_and_completes(hass: HomeAssistant) -> None:
    await _store_year(
        hass, 2026, [_session(status="followup_open", open_fields=("soc_start", "cost"))]
    )

    updated = await session_manager.async_close_followup(hass, SESSION_ID)

    assert updated.open_fields == ()
    assert updated.status == "complete"


async def test_close_followup_keeps_a_flagged_session_flagged(hass: HomeAssistant) -> None:
    """A session flagged for a data-quality reason stays flagged after its gaps are accepted."""
    await _store_year(hass, 2026, [_session(status="flagged", open_fields=("odometer_km",))])

    updated = await session_manager.async_close_followup(hass, SESSION_ID)

    assert updated.open_fields == ()
    assert updated.status == "flagged"


# ----------------------------------------------------------------------- correct_vehicle


async def test_correct_vehicle_rejects_an_unknown_vehicle(hass: HomeAssistant) -> None:
    await _store_year(hass, 2026, [_session()])

    with pytest.raises(session_manager.SessionValidationError):
        await session_manager.async_correct_vehicle(hass, SESSION_ID, "does-not-exist")


async def test_correct_vehicle_reassigns_and_keeps_energy_cost_and_phases(
    hass: HomeAssistant,
) -> None:
    """7.8: energy, cost and phases are kept; the card stays as actually read."""
    _add_vehicle(hass, Vehicle(id="v002", name="EQB", capacity_kwh=70.5))
    await _store_year(
        hass,
        2026,
        [
            _session(
                vehicle_id="v001",
                vehicle_name="GLB",
                capacity_kwh=85.0,
                card_uid="AABBCCDD",
                card_label="Card GLB",
                energy_measured_kwh=10.0,
                energy_kwh=10.0,
                cost=3.0,
                phases=(Phase(start="2026-06-01T10:00:00+02:00"),),
            )
        ],
    )

    updated = await session_manager.async_correct_vehicle(hass, SESSION_ID, "v002")

    assert updated.vehicle_id == "v002"
    assert updated.vehicle_name == "EQB"
    assert updated.capacity_kwh == 70.5
    assert updated.identification_corrected is True
    assert updated.card_uid == "AABBCCDD"
    assert updated.card_label == "Card GLB"
    assert updated.energy_measured_kwh == 10.0
    assert updated.energy_kwh == 10.0
    assert updated.cost == 3.0
    assert len(updated.phases) == 1


async def test_correct_vehicle_resolves_a_previously_unassigned_session(
    hass: HomeAssistant,
) -> None:
    """7.8: the same path resolves an unresolved session; no second mechanism exists."""
    _add_vehicle(hass, Vehicle(id="v002", name="EQB", capacity_kwh=70.5))
    await _store_year(
        hass,
        2026,
        [
            _session(
                id="2026-06-01T10:00:00_unresolved",
                vehicle_id=None,
                vehicle_name=None,
                capacity_kwh=None,
                status="followup_open",
                open_fields=("vehicle_id",),
            )
        ],
    )

    updated = await session_manager.async_correct_vehicle(
        hass, "2026-06-01T10:00:00_unresolved", "v002"
    )

    assert updated.vehicle_id == "v002"
    assert "vehicle_id" not in updated.open_fields


async def test_correct_vehicle_leaves_unresolvable_start_values_open(
    hass: HomeAssistant,
) -> None:
    """Without a recorder answer, soc_start and odometer_km go to open_fields (7.8)."""
    _add_vehicle(
        hass,
        Vehicle(
            id="v002",
            name="EQB",
            capacity_kwh=70.5,
            soc=EntityRole(entity_id="sensor.eqb_soc"),
            odometer=EntityRole(entity_id="sensor.eqb_odometer"),
        ),
    )
    await _store_year(hass, 2026, [_session()])

    updated = await session_manager.async_correct_vehicle(hass, SESSION_ID, "v002")

    assert updated.soc_start is None
    assert updated.odometer_km is None
    assert "soc_start" in updated.open_fields
    assert "odometer_km" in updated.open_fields
    assert updated.status == "followup_open"


async def test_correct_vehicle_reads_start_values_from_the_recorder(hass: HomeAssistant) -> None:
    """7.8: soc_start and odometer_km are re-read from the new vehicle's history."""
    _add_vehicle(
        hass,
        Vehicle(
            id="v002",
            name="EQB",
            capacity_kwh=70.5,
            soc=EntityRole(entity_id="sensor.eqb_soc"),
            odometer=EntityRole(entity_id="sensor.eqb_odometer"),
        ),
    )
    await _store_year(hass, 2026, [_session(soc_end=90.0)])

    with _mock_history({"sensor.eqb_soc": ("55", "%"), "sensor.eqb_odometer": ("12345", "km")}):
        updated = await session_manager.async_correct_vehicle(hass, SESSION_ID, "v002")

    assert updated.soc_start == pytest.approx(55.0)
    assert updated.odometer_km == pytest.approx(12345.0)
    assert updated.soc_end == 90.0  # not re-determined, per 7.8's correction table
    assert updated.status == "complete"


async def test_correct_vehicle_never_raises_when_the_recorder_is_unavailable(
    hass: HomeAssistant,
) -> None:
    """A failed recorder lookup degrades to open_fields, never a crash (Robustheit)."""
    _add_vehicle(
        hass,
        Vehicle(
            id="v002",
            name="EQB",
            capacity_kwh=70.5,
            soc=EntityRole(entity_id="sensor.eqb_soc"),
            odometer=EntityRole(entity_id="sensor.eqb_odometer"),
        ),
    )
    await _store_year(hass, 2026, [_session()])

    with patch(
        "custom_components.ev_charging.session_manager.history.state_changes_during_period",
        side_effect=KeyError("recorder_instance"),
    ):
        updated = await session_manager.async_correct_vehicle(hass, SESSION_ID, "v002")

    assert updated.soc_start is None
    assert updated.odometer_km is None
    assert "soc_start" in updated.open_fields
    assert "odometer_km" in updated.open_fields
    assert updated.status == "followup_open"


# --------------------------------------------------------- late resolution via the recorder


async def test_a_late_resolved_session_gets_its_start_values_from_the_recorder(
    hass: HomeAssistant, freezer: Any
) -> None:
    """7.8: the automatic late resolution (Etappe 6/7) now uses the recorder too."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    await _setup_manager(hass, vehicles=(_glb(), _eqb()))

    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)
    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"

    with _mock_history({GLB_SOC: ("40", "%"), GLB_ODO: ("7699", "km")}):
        await _set(hass, GLB_CHARGE, "13")
        await _set(hass, EQB_CHARGE, "3")
        await hass.async_block_till_done()

        await _unplug(hass, freezer)

    (session,) = await _stored(hass)
    assert session.vehicle_id == "v001"
    assert session.soc_start == pytest.approx(40.0)
    assert session.odometer_km == pytest.approx(7699.0)
    assert "soc_start" not in session.open_fields
    assert "odometer_km" not in session.open_fields
    assert session.status == "complete"


# ----------------------------------------------------------------------- create_session


async def test_create_session_requires_a_complete_period(hass: HomeAssistant) -> None:
    with pytest.raises(session_manager.SessionValidationError):
        await session_manager.async_create_session(
            hass,
            {
                "location": "external",
                "plug_start": dt_util.parse_datetime("2026-06-01T10:00:00+02:00"),
                "plug_end": dt_util.parse_datetime("2026-06-01T09:00:00+02:00"),
            },
        )


async def test_create_session_rejects_an_unknown_vehicle(hass: HomeAssistant) -> None:
    with pytest.raises(session_manager.SessionValidationError):
        await session_manager.async_create_session(
            hass,
            {
                "location": "external",
                "plug_start": dt_util.parse_datetime("2026-06-01T10:00:00+02:00"),
                "plug_end": dt_util.parse_datetime("2026-06-01T12:00:00+02:00"),
                "vehicle_id": "does-not-exist",
            },
        )


async def test_create_session_with_only_the_required_fields_is_followup_open(
    hass: HomeAssistant,
) -> None:
    """A minimal manual entry is stored, but marked as still needing values (13, 16)."""
    created = await session_manager.async_create_session(
        hass,
        {
            "location": "external",
            "plug_start": dt_util.parse_datetime("2026-06-01T10:00:00+02:00"),
            "plug_end": dt_util.parse_datetime("2026-06-01T12:00:00+02:00"),
        },
    )

    assert created.identification_source == "unresolved"
    assert created.status == "followup_open"
    assert set(created.open_fields) >= {"vehicle_id", "soc_start", "soc_end", "energy_kwh", "cost"}
    assert created.phases_recorded is False
    assert len(created.phases) == 1
    assert created.plug_duration_min == pytest.approx(120.0)
    (stored,) = await SessionYearStore(hass, 2026).async_load()
    assert stored.id == created.id


async def test_create_session_with_full_fields_is_complete_and_manual(
    hass: HomeAssistant,
) -> None:
    _add_vehicle(hass, Vehicle(id="v001", name="GLB", capacity_kwh=85.0))

    created = await session_manager.async_create_session(
        hass,
        {
            "location": "external",
            "plug_start": dt_util.parse_datetime("2026-06-01T10:00:00+02:00"),
            "plug_end": dt_util.parse_datetime("2026-06-01T12:00:00+02:00"),
            "vehicle_id": "v001",
            "soc_start": 40.0,
            "soc_end": 80.0,
            "odometer_km": 7000.0,
            "cost": 12.5,
        },
    )

    assert created.identification_source == "manual"
    assert created.vehicle_name == "GLB"
    assert created.capacity_kwh == 85.0
    assert created.energy_raw_kwh == pytest.approx(34.0)
    assert created.energy_kwh == pytest.approx(34.0)
    assert created.status == "complete"
    assert created.open_fields == ()


async def test_create_session_prefers_the_billed_energy_over_the_soc_estimate(
    hass: HomeAssistant,
) -> None:
    """8.4: energy_billed_kwh outranks the ΔSOC estimate when both are given."""
    _add_vehicle(hass, Vehicle(id="v001", name="GLB", capacity_kwh=85.0))

    created = await session_manager.async_create_session(
        hass,
        {
            "location": "external",
            "plug_start": dt_util.parse_datetime("2026-06-01T10:00:00+02:00"),
            "plug_end": dt_util.parse_datetime("2026-06-01T12:00:00+02:00"),
            "vehicle_id": "v001",
            "soc_start": 40.0,
            "soc_end": 80.0,
            "energy_billed_kwh": 30.0,
        },
    )

    assert created.energy_raw_kwh == pytest.approx(34.0)
    assert created.energy_billed_kwh == 30.0
    assert created.energy_kwh == pytest.approx(30.0)


async def test_create_session_at_home_defaults_the_charge_type_from_the_wallbox(
    hass: HomeAssistant,
) -> None:
    """Mirrors the legacy import (16): a home session without charge_type takes the wallbox's."""
    _add_wallbox(hass, Wallbox(id="wb001", name="Carport", current_type="ac", max_power_kw=11.0))

    created = await session_manager.async_create_session(
        hass,
        {
            "location": "home",
            "plug_start": dt_util.parse_datetime("2026-06-01T10:00:00+02:00"),
            "plug_end": dt_util.parse_datetime("2026-06-01T12:00:00+02:00"),
        },
    )

    assert created.charge_type == "ac"
    assert created.charge_type_source == "wallbox_config"
    assert created.wallbox_id == "wb001"


async def test_create_session_assigns_the_year_of_the_local_plug_start(
    hass: HomeAssistant,
) -> None:
    """I10: the year store follows plug_start in local time, not UTC."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    created = await session_manager.async_create_session(
        hass,
        {
            "location": "external",
            # 23:30 UTC on 31 December is 00:30 on 1 January in Berlin.
            "plug_start": dt_util.parse_datetime("2026-12-31T23:30:00+00:00"),
            "plug_end": dt_util.parse_datetime("2027-01-01T01:00:00+00:00"),
        },
    )

    await _touch_year_file(hass, 2027)
    stored_2027 = await SessionYearStore(hass, 2027).async_load()
    assert [s.id for s in stored_2027] == [created.id]
