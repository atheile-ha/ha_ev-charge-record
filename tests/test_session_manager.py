"""Tests for the session capture at the wallbox."""

from __future__ import annotations

import logging
import os
from datetime import timedelta
from typing import Any

import pytest
from custom_components.ev_charging import problems
from custom_components.ev_charging.const import (
    DOMAIN,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
    store_key_sessions,
)
from custom_components.ev_charging.models import Card, EntityRole, HubSettings, Vehicle, Wallbox
from custom_components.ev_charging.session_manager import (
    SessionManager,
    StepKind,
    counter_step,
    energy_raw_kwh,
    identify,
)
from custom_components.ev_charging.store import SessionYearStore
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

TIME_ZONE = "Europe/Berlin"

POWER = "sensor.wb_power"
TOTAL = "sensor.wb_energy_total"
SESSION = "sensor.wb_energy_session"
PLUG = "sensor.wb_plug"
ERROR = "sensor.wb_error"
CARD = "sensor.wb_card"
GRID = "sensor.house_grid"
GLB_CHARGE = "sensor.glb_charging"
GLB_SOC = "sensor.glb_soc"
GLB_ODO = "sensor.glb_odometer"
GLB_TRACKER = "device_tracker.glb"
EQB_TRACKER = "device_tracker.eqb"
EQB_CHARGE = "sensor.eqb_charging"

GLB_CARD = "AABBCCDD11223344"
EQB_CARD = "0011223344556677"

PLUGGED = "plugged_and_locked"
UNPLUGGED = "unplugged"


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Give the test a private config dir: the years with data are read from disk."""
    return hass_tmp_config_dir


@pytest.fixture(autouse=True)
async def _time_zone(hass: HomeAssistant) -> None:
    """Use a fixed time zone."""
    await hass.config.async_set_time_zone(TIME_ZONE)


def _role(entity_id: str, unit: str | None = None) -> EntityRole:
    return EntityRole(entity_id=entity_id, registry_entry_id=None, unit=unit)


def _wallbox(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "id": "wb001",
        "name": "Carport",
        "current_type": "ac",
        "max_power_kw": 11.0,
        "power_threshold_kw": 0.5,
        "start_debounce_s": 2,
        "identification_window_s": 15,
        "mapping_id": "openems_keba_p40",
        "charge_power": _role(POWER, "kW"),
        "energy_total": _role(TOTAL, "kWh"),
        "plug_state": _role(PLUG),
        "error": _role(ERROR),
        "identification": _role(CARD),
    }
    fields.update(overrides)
    return Wallbox(**fields).to_dict()


def _both_counters() -> dict[str, Any]:
    """A wallbox that reports the total and the session energy counter."""
    return _wallbox(energy_session=_role(SESSION, "kWh"))


def _glb(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "id": "v001",
        "name": "GLB",
        "capacity_kwh": 85.0,
        "cards": (Card(uid=GLB_CARD, label="Card GLB"),),
        "identify_by_vehicle_api": True,
        "mapping_id": "mbapi2020_mercedes_me",
        "vin": "W1NSYNTHETIC000001",
        "soc": _role(GLB_SOC, "%"),
        "odometer": _role(GLB_ODO, "km"),
        "charge_state": _role(GLB_CHARGE),
        "location": _role(GLB_TRACKER),
    }
    fields.update(overrides)
    return Vehicle(**fields).to_dict()


def _eqb(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "id": "v002",
        "name": "EQB",
        "capacity_kwh": 70.5,
        "cards": (Card(uid=EQB_CARD, label="Card EQB"),),
        "identify_by_vehicle_api": True,
        "mapping_id": "mbapi2020_mercedes_me",
        "charge_state": _role(EQB_CHARGE),
        "location": _role(EQB_TRACKER),
    }
    fields.update(overrides)
    return Vehicle(**fields).to_dict()


def _hub(**overrides: Any) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "grid_power": _role(GRID, "W"),
        "price_grid_fixed": 0.30,
        "price_feed_in_fixed": 0.08,
    }
    settings.update(overrides)
    return {"wallbox_seq": 1, "vehicle_seq": 2, **HubSettings(**settings).to_dict()}


def _subentry(subentry_type: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "data": data,
        "subentry_type": subentry_type,
        "title": data["name"],
        "unique_id": None,
    }


async def _setup(
    hass: HomeAssistant,
    *,
    wallbox: dict[str, Any] | None = None,
    vehicles: tuple[dict[str, Any], ...] = (),
    hub: dict[str, Any] | None = None,
    start_states: bool = True,
) -> tuple[MockConfigEntry, SessionManager]:
    """Set up the integration with a wallbox and vehicles, all sources idle."""
    if start_states:
        hass.states.async_set(PLUG, UNPLUGGED)
        hass.states.async_set(POWER, "0", {"unit_of_measurement": "kW"})
        hass.states.async_set(TOTAL, "100.0", {"unit_of_measurement": "kWh"})
        hass.states.async_set(SESSION, "0.0", {"unit_of_measurement": "kWh"})
        hass.states.async_set(ERROR, "not_ready_for_charging")
        hass.states.async_set(CARD, "0")
        hass.states.async_set(GRID, "0", {"unit_of_measurement": "W"})
        hass.states.async_set(GLB_TRACKER, "unknown")
        hass.states.async_set(EQB_TRACKER, "unknown")
        hass.states.async_set(GLB_CHARGE, "3")
        hass.states.async_set(EQB_CHARGE, "3")
        hass.states.async_set(GLB_SOC, "40", {"unit_of_measurement": "%"})
        hass.states.async_set(GLB_ODO, "7699", {"unit_of_measurement": "km"})
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=hub or _hub(),
        version=4,
        minor_version=1,
        subentries_data=[
            _subentry(SUBENTRY_TYPE_WALLBOX, wallbox or _wallbox()),
            *(_subentry(SUBENTRY_TYPE_VEHICLE, vehicle) for vehicle in vehicles),
        ],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    manager = entry.runtime_data.manager
    assert manager is not None
    return entry, manager


async def _set(hass: HomeAssistant, entity_id: str, value: str, unit: str | None = None) -> None:
    attributes = {"unit_of_measurement": unit} if unit else {}
    hass.states.async_set(entity_id, value, attributes)
    await hass.async_block_till_done()


async def _advance(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: float) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def _start_charging(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, power_kw: float = 7.0
) -> None:
    """Plug in, start charging and let the debounce pass."""
    await _set(hass, PLUG, PLUGGED)
    await _set(hass, POWER, str(power_kw), "kW")
    await _advance(hass, freezer, 2)


async def _unplug(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Unplug and let the wait for final values pass."""
    await _set(hass, POWER, "0", "kW")
    await _set(hass, PLUG, UNPLUGGED)
    await _advance(hass, freezer, 3)


async def _stored(hass: HomeAssistant, year: int = 2026) -> list:
    return await SessionYearStore(hass, year).async_load()


async def _touch_year_file(hass: HomeAssistant, year: int) -> None:
    """Create the file the scan for years with data looks for."""

    def _touch() -> None:
        storage_dir = hass.config.path(".storage")
        os.makedirs(storage_dir, exist_ok=True)
        open(os.path.join(storage_dir, store_key_sessions(year)), "a", encoding="utf-8").close()

    await hass.async_add_executor_job(_touch)


def _issue(hass: HomeAssistant, issue_id: str) -> ir.IssueEntry | None:
    return ir.async_get(hass).async_get_issue(DOMAIN, issue_id)


def _wallbox_subentry_id(entry: MockConfigEntry) -> str:
    return next(
        subentry.subentry_id
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_WALLBOX
    )


# --------------------------------------------------------------- pure functions


def test_counter_step_accumulates_a_plausible_increase() -> None:
    """A normal increase within what the wallbox can deliver is accumulated."""
    step = counter_step(100.0, 100.5, max_power_kw=11.0, elapsed_s=300)

    assert step.kind is StepKind.NORMAL
    assert step.delta_kwh == pytest.approx(0.5)


def test_counter_step_treats_a_decrease_as_reset() -> None:
    """A negative step means the counter restarted; the new value counts in full."""
    step = counter_step(48.2, 0.4, max_power_kw=11.0, elapsed_s=300)

    assert step.kind is StepKind.RESET
    assert step.delta_kwh == pytest.approx(0.4)


def test_counter_step_rejects_an_impossible_jump() -> None:
    """A jump the wallbox could not have delivered is not accumulated at all."""
    step = counter_step(100.0, 1000.0, max_power_kw=11.0, elapsed_s=300)

    assert step.kind is StepKind.IMPLAUSIBLE
    assert step.delta_kwh == 0.0


def test_counter_step_allows_the_power_tolerance() -> None:
    """The nominal power is regularly exceeded by a little, which is not a jump."""
    limit_kwh = 11.0 * 1.15 * 600 / 3600

    assert counter_step(0.0, limit_kwh - 0.01, max_power_kw=11.0, elapsed_s=600).delta_kwh > 0
    assert counter_step(0.0, limit_kwh + 0.01, max_power_kw=11.0, elapsed_s=600).delta_kwh == 0


def test_counter_step_does_not_flag_a_coarse_counter_ticking_quickly() -> None:
    """One tick of a coarse counter shortly after the last one is not a jump."""
    assert counter_step(5.0, 5.1, max_power_kw=11.0, elapsed_s=2).kind is StepKind.NORMAL


def test_energy_raw_is_the_state_of_charge_difference_without_factor() -> None:
    """The raw energy carries no efficiency factor."""
    assert energy_raw_kwh(40, 60, 85.0) == pytest.approx(17.0)
    assert energy_raw_kwh(None, 60, 85.0) is None
    assert energy_raw_kwh(40, 60, None) is None


def _vehicle(vehicle_id: str, *cards: Card, api: bool = False, active: bool = True) -> Vehicle:
    return Vehicle(
        id=vehicle_id, name=vehicle_id, active=active, cards=cards, identify_by_vehicle_api=api
    )


def test_identify_by_full_card() -> None:
    """A reported value equal to a stored card identifies its vehicle."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"))

    result = identify(GLB_CARD, [glb], set())

    assert (result.source, result.vehicle_id, result.card_uid) == ("rfid", "v001", GLB_CARD)


def test_identify_by_the_end_of_a_card() -> None:
    """The wallbox reports only the end of the printed serial number."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"))

    result = identify("11223344", [glb], set())

    assert result.vehicle_id == "v001"
    assert result.card_uid == GLB_CARD


def test_identify_uses_the_card_type_as_source() -> None:
    """An eMAID card gives the source emaid."""
    vehicle = _vehicle("v001", Card(uid=GLB_CARD, label="a", type="emaid"))

    assert identify(GLB_CARD, [vehicle], set()).source == "emaid"


def test_identify_ignores_the_start_of_a_card() -> None:
    """A value that is the start of a card and not its end is no match."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"))

    result = identify("AABBCCDD", [glb], set())

    assert result.vehicle_id is None
    assert result.unknown_card is True


def test_identify_ambiguous_ending_is_no_match() -> None:
    """An ending that fits two cards names no vehicle and hands over to the next stage."""
    first = _vehicle("v001", Card(uid="AAAA11223344", label="a"))
    second = _vehicle("v002", Card(uid="BBBB11223344", label="b"))

    result = identify("11223344", [first, second], set())

    assert result.vehicle_id is None
    assert result.unknown_card is False
    assert result.card_uid == "11223344"


def test_identify_ambiguous_ending_falls_back_to_the_vehicle_report() -> None:
    """After an ambiguous ending the vehicle's own report can still identify it."""
    first = _vehicle("v001", Card(uid="AAAA11223344", label="a"), api=True)
    second = _vehicle("v002", Card(uid="BBBB11223344", label="b"), api=True)

    result = identify("11223344", [first, second], {"v002"})

    assert (result.source, result.vehicle_id) == ("vehicle_api", "v002")


def test_identify_unknown_card_stops_the_cascade() -> None:
    """A card nobody holds is someone else's; the vehicle report must not claim the session."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"), api=True)

    result = identify("DEADBEEF", [glb], {"v001"})

    assert result.source == "unresolved"
    assert result.vehicle_id is None
    assert result.unknown_card is True
    assert result.card_uid == "DEADBEEF"


def test_identify_ignores_inactive_vehicles_and_cards() -> None:
    """Only active cards of active vehicles count."""
    inactive_vehicle = _vehicle("v001", Card(uid=GLB_CARD, label="a"), active=False)
    inactive_card = _vehicle("v002", Card(uid=EQB_CARD, label="b", active=False))

    assert identify(GLB_CARD, [inactive_vehicle], set()).unknown_card is True
    assert identify(EQB_CARD, [inactive_card], set()).unknown_card is True


def test_identify_by_vehicle_report_needs_exactly_one_vehicle_at_home() -> None:
    """One vehicle at home identifies; two vehicles at home name none."""
    first = _vehicle("v001", api=True)
    second = _vehicle("v002", api=True)

    assert identify(None, [first, second], {"v001"}).vehicle_id == "v001"
    assert identify(None, [first, second], {"v001", "v002"}).vehicle_id is None
    assert identify(None, [first, second], set()).source == "unresolved"


def test_card_and_vehicle_report_that_disagree_are_a_conflict_and_the_card_wins() -> None:
    """The card names one vehicle while another reports being at home."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"), api=True)
    eqb = _vehicle("v002", api=True)

    result = identify(GLB_CARD, [glb, eqb], {"v002"})

    assert result.vehicle_id == "v001"
    assert result.conflict is True


def test_card_and_vehicle_report_that_agree_are_no_conflict() -> None:
    """The card and the vehicle name the same vehicle."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"), api=True)

    assert identify(GLB_CARD, [glb], {"v001"}).conflict is False


def test_no_vehicle_is_chosen_because_the_others_are_absent() -> None:
    """A vehicle that says nothing is never picked by elimination."""
    silent = _vehicle("v001", api=True)
    away = _vehicle("v002", api=True)

    result = identify(None, [silent, away], set())

    assert result.vehicle_id is None
    assert result.source == "unresolved"


# ------------------------------------------------------------------ candidate


async def test_candidate_is_published_at_once(hass: HomeAssistant) -> None:
    """The candidate state and the session flag appear the moment the power rises."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)

    await _set(hass, POWER, "7.0", "kW")

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "candidate"
    assert hass.states.get("binary_sensor.ev_charging_wallbox_session").state == "on"


async def test_candidate_becomes_a_session_after_the_debounce(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The candidate turns into a running session once the power held."""
    await _setup(hass)

    await _start_charging(hass, freezer)

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"


async def test_candidate_is_dropped_when_the_power_falls_back(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A brief peak leaves no session behind."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _set(hass, POWER, "7.0", "kW")

    await _set(hass, POWER, "0.1", "kW")
    await _advance(hass, freezer, 5)

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "idle"
    assert hass.states.get("binary_sensor.ev_charging_wallbox_session").state == "off"
    assert await _stored(hass) == []


async def test_a_zero_debounce_confirms_immediately(hass: HomeAssistant) -> None:
    """Without a debounce time the session runs right away."""
    await _setup(hass, wallbox=_wallbox(start_debounce_s=0))
    await _set(hass, PLUG, PLUGGED)

    await _set(hass, POWER, "7.0", "kW")

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"


async def test_no_candidate_while_the_connector_reports_not_connected(
    hass: HomeAssistant,
) -> None:
    """Power alone does not start a session while the wallbox says nothing is plugged in."""
    await _setup(hass)

    await _set(hass, POWER, "7.0", "kW")

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "idle"


# ---------------------------------------------------------------- one session


async def test_power_dropping_and_rising_again_makes_one_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Below the threshold and back above it, with the plug connected throughout: one session."""
    await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, POWER, "0.0", "kW")
    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "paused"
    await _advance(hass, freezer, 120)
    await _set(hass, POWER, "6.5", "kW")
    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"
    await _set(hass, POWER, "0.0", "kW")
    await _advance(hass, freezer, 120)
    await _set(hass, POWER, "5.0", "kW")
    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].phase_count == 1


async def test_a_pause_of_the_minimum_length_splits_the_phase(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """After a pause of at least 15 minutes the next charging is a new phase of the same session."""
    await _setup(hass)
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 300)

    await _set(hass, POWER, "0.0", "kW")
    await _advance(hass, freezer, 16 * 60)
    await _set(hass, POWER, "6.0", "kW")
    await _advance(hass, freezer, 300)
    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    session = sessions[0]
    assert session.phase_count == 2
    assert session.pause_duration_min == pytest.approx(16.0, abs=0.5)
    assert session.charge_duration_min == pytest.approx(
        sum(phase.duration_min for phase in session.phases), abs=0.2
    )


# ---------------------------------------------------------------------- ending


async def test_only_disconnecting_ends_a_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """No power for hours does not end a session; unplugging does."""
    await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, POWER, "0.0", "kW")
    await _advance(hass, freezer, 5 * 3600)

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "paused"
    assert await _stored(hass) == []

    await _unplug(hass, freezer)
    assert len(await _stored(hass)) == 1
    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "idle"


async def test_a_neutral_plug_value_keeps_the_session_open_without_a_repair_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A value the mapping marks neutral leaves the last class in force."""
    entry, _ = await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, PLUG, "undefined")
    await _advance(hass, freezer, 60)

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"
    assert await _stored(hass) == []
    issue_id = problems.unknown_mapping_value_issue_id(_wallbox_subentry_id(entry), "plug_state")
    assert _issue(hass, issue_id) is None


async def test_an_unmapped_plug_value_keeps_the_session_open_and_raises_an_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A value missing from the mapping never ends a session, and is reported."""
    entry, _ = await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, PLUG, "some_new_value")
    await _advance(hass, freezer, 60)

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"
    assert await _stored(hass) == []
    issue_id = problems.unknown_mapping_value_issue_id(_wallbox_subentry_id(entry), "plug_state")
    assert _issue(hass, issue_id) is not None


async def test_an_unavailable_plug_state_does_not_end_a_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A source that drops out for a while leaves the session open."""
    await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, PLUG, "unavailable")
    await _advance(hass, freezer, 3600)

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"
    assert await _stored(hass) == []


async def test_a_lasting_outage_of_the_plug_state_closes_the_session_flagged(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """After 12 hours without a usable plug state the session is closed and flagged."""
    await _setup(hass)
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 600)
    await _set(hass, PLUG, "unavailable")
    outage_start = dt_util.utcnow()

    await _advance(hass, freezer, 12 * 3600 + 5)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    session = sessions[0]
    assert session.status == "flagged"
    assert "soc_end" in session.open_fields
    assert dt_util.parse_datetime(session.plug_end) <= outage_start


async def test_a_neutral_value_does_not_count_as_unavailable_for_the_timeout(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A neutral value is a value; it restarts the wait instead of adding to the outage."""
    await _setup(hass)
    await _start_charging(hass, freezer)
    await _set(hass, PLUG, "unavailable")
    await _advance(hass, freezer, 11 * 3600)

    await _set(hass, PLUG, "undefined")
    await _advance(hass, freezer, 3 * 3600)

    assert await _stored(hass) == []
    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"


async def test_a_charging_error_does_not_end_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A reported error puts the session in the error state and leaves it open."""
    await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "error"
    assert await _stored(hass) == []

    await _set(hass, ERROR, "charging")
    await _set(hass, POWER, "6.0", "kW")
    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"

    await _unplug(hass, freezer)
    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].charge_error is True


async def test_an_error_that_clears_before_the_debounce_is_ignored(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A brief error report does not change the state."""
    await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 2)
    await _set(hass, ERROR, "charging")
    await _advance(hass, freezer, 10)

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"


async def test_a_neutral_error_value_keeps_the_error_class(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The neutral value of the error role neither raises nor clears an error."""
    await _setup(hass)
    await _start_charging(hass, freezer)
    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)

    await _set(hass, ERROR, "undefined")

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "error"


# ----------------------------------------------------------------------- energy


async def test_energy_grid_solar_and_cost_are_recorded(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The energy is split by the grid balance and valued with both prices."""
    await _setup(hass, wallbox=_both_counters())
    await _set(hass, GRID, "3000", "W")
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")
    await _set(hass, SESSION, "1.0", "kWh")
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "102.0", "kWh")
    await _set(hass, SESSION, "2.0", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.energy_measured_kwh == pytest.approx(2.0)
    assert session.energy_measured_session_kwh == pytest.approx(2.0)
    assert session.energy_kwh == pytest.approx(2.0)
    assert session.energy_grid_kwh == pytest.approx(1.0)
    assert session.energy_solar_kwh == pytest.approx(1.0)
    assert session.cost == pytest.approx(1.0 * 0.30 + 1.0 * 0.08)
    assert session.energy_unallocated_kwh == 0.0
    assert session.charge_type == "ac"
    assert session.charge_type_source == "wallbox_config"
    assert session.location == "home"
    assert session.wallbox_id == "wb001"
    assert session.phases_recorded is True
    assert sum(phase.energy_kwh for phase in session.phases) == pytest.approx(2.0)


async def test_solar_valuation_zero_makes_the_sun_free(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """With the solar share valued at zero only the grid share costs."""
    await _setup(hass, hub=_hub(solar_valuation="zero"))
    await _set(hass, GRID, "3000", "W")
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "102.0", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.cost == pytest.approx(session.energy_grid_kwh * 0.30)


async def test_without_a_grid_balance_the_energy_is_not_split_but_valued_at_the_grid_price(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """No grid balance: no split, all energy at the grid price."""
    await _setup(hass, hub=_hub(grid_power=None))
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.energy_grid_kwh is None
    assert session.energy_solar_kwh is None
    assert session.cost == pytest.approx(0.30)


async def test_without_prices_there_is_no_cost(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Without a grid price no cost is determined."""
    await _setup(hass, hub=_hub(price_grid_fixed=None, price_feed_in_fixed=None))
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.cost is None
    assert session.energy_measured_kwh == pytest.approx(1.0)


async def test_a_price_from_an_entity_is_used_and_the_last_valid_price_is_kept(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A price entity that becomes unavailable does not stop the valuation."""
    price = "sensor.price_grid"
    hass.states.async_set(price, "0.40", {"unit_of_measurement": "EUR/kWh"})
    await _setup(
        hass,
        hub=_hub(
            grid_power=None,
            price_grid=_role(price, "EUR/kWh"),
            price_grid_fixed=None,
            price_feed_in_fixed=None,
        ),
    )
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, price, "unavailable")
    await _set(hass, TOTAL, "101.0", "kWh")

    await _unplug(hass, freezer)

    assert (await _stored(hass))[0].cost == pytest.approx(0.40)


@pytest.mark.parametrize("mode", ["dynamic", "static"])
async def test_cost_is_dynamic_whatever_the_vehicle_cost_mode(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, mode: str
) -> None:
    """The cost mode of a vehicle has no effect on the capture."""
    await _setup(hass, vehicles=(_glb(cost_mode=mode),), hub=_hub(grid_power=None))
    await _set(hass, CARD, GLB_CARD)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.vehicle_id == "v001"
    assert session.cost == pytest.approx(0.30)


async def test_energy_grid_cannot_be_split_while_no_share_is_known(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Energy that arrives before any grid balance is known is booked as unallocated."""
    await _setup(hass)
    await _set(hass, GRID, "unavailable")
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)

    await _set(hass, TOTAL, "101.0", "kWh")
    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.energy_measured_kwh == pytest.approx(1.0)
    assert session.energy_unallocated_kwh == pytest.approx(1.0)
    assert session.energy_grid_kwh == pytest.approx(0.0)


async def test_a_counter_reset_is_accumulated_as_new_energy(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A counter that restarts from zero does not lose or duplicate energy."""
    await _setup(hass)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "0.5", "kWh")
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "1.0", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.energy_measured_kwh == pytest.approx(1.0 + 0.5 + 0.5)
    assert session.status == "followup_open"


async def test_an_impossible_jump_is_not_accumulated_and_flags_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A scale change of the counter must not become energy."""
    await _setup(hass)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "1020.0", "kWh")
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "1021.0", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.status == "flagged"
    assert session.energy_measured_kwh == pytest.approx(2.0)


async def test_counters_that_disagree_flag_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """More than five percent between the two counters flags the session; the total stays."""
    await _setup(hass, wallbox=_both_counters())
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "102.0", "kWh")
    await _set(hass, SESSION, "1.5", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.status == "flagged"
    assert session.energy_measured_kwh == pytest.approx(2.0)
    assert session.energy_measured_session_kwh == pytest.approx(1.5)


async def test_an_energy_above_what_the_wallbox_can_deliver_flags_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Energy above the maximum power over the plug time is impossible."""
    await _setup(hass)
    await _start_charging(hass, freezer, power_kw=6.0)
    for step in range(1, 11):
        await _advance(hass, freezer, 10)
        await _set(hass, TOTAL, f"{100 + step * 0.2}", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.energy_measured_kwh == pytest.approx(2.0)
    assert session.status == "flagged"


async def test_a_stalled_authoritative_counter_is_replaced_by_the_other(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The total counter stands still while the session counter rises: switch over."""
    entry, _ = await _setup(hass, wallbox=_both_counters())
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 60)
    await _set(hass, SESSION, "0.1", "kWh")
    await _advance(hass, freezer, 60)
    await _set(hass, SESSION, "0.2", "kWh")
    await _advance(hass, freezer, 60)
    await _set(hass, SESSION, "0.3", "kWh")
    await _advance(hass, freezer, 60)

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.energy_measured_kwh == pytest.approx(0.3)
    issue_id = problems.counter_switched_issue_id(_wallbox_subentry_id(entry))
    assert _issue(hass, issue_id) is not None


async def test_the_energy_estimate_carries_no_efficiency_factor(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The raw energy is the state of charge difference times the capacity, nothing else."""
    await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, GLB_CARD)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 20)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")
    await _set(hass, GLB_SOC, "60", "%")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.soc_start == 40
    assert session.soc_end == 60
    assert session.energy_raw_kwh == pytest.approx(17.0)
    assert session.energy_estimated_kwh is None
    assert session.energy_kwh == pytest.approx(1.0)
    assert session.energy_measured_kwh == pytest.approx(1.0)
    assert session.odometer_km == 7699
    assert session.capacity_kwh == 85.0


# --------------------------------------------------------------- identification


async def test_a_known_card_assigns_the_vehicle_after_the_window(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The card decides the vehicle when the identification window has passed."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _set(hass, CARD, "11223344")
    await _start_charging(hass, freezer)
    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "unresolved"

    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "GLB"
    await _unplug(hass, freezer)
    session = (await _stored(hass))[0]
    assert session.vehicle_id == "v001"
    assert session.vehicle_name == "GLB"
    assert session.identification_source == "rfid"
    assert session.card_uid == GLB_CARD
    assert session.card_label == "Card GLB"
    assert session.id.endswith("_v001")


async def test_an_unknown_card_leaves_the_session_unassigned_and_raises_an_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A card no vehicle holds: the session is recorded in full, unassigned, and reported."""
    entry, _ = await _setup(hass, vehicles=(_glb(), _eqb()))
    await _set(hass, GLB_TRACKER, "home")
    await _set(hass, CARD, "DEADBEEF")
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.vehicle_id is None
    assert session.identification_source == "unresolved"
    assert session.status == "followup_open"
    assert session.card_uid == "DEADBEEF"
    assert session.energy_measured_kwh == pytest.approx(1.0)
    assert session.energy_solar_kwh == pytest.approx(1.0)
    assert session.cost == pytest.approx(0.08)
    assert session.id.endswith("_unresolved")
    assert _issue(hass, problems.unknown_card_issue_id(_wallbox_subentry_id(entry))) is not None


async def test_a_stale_card_value_does_not_identify(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A card value that last changed long before the session start is not evidence."""
    await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, GLB_CARD)
    await _advance(hass, freezer, 3600)

    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "unresolved"


async def test_an_empty_card_value_is_no_card(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The values 0, unknown and unavailable never count as a card."""
    entry, _ = await _setup(hass, vehicles=(_glb(),))
    for value in ("0", "unknown", "unavailable", ""):
        await _set(hass, CARD, value)
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "unresolved"
    assert _issue(hass, problems.unknown_card_issue_id(_wallbox_subentry_id(entry))) is None


async def test_the_vehicle_report_identifies_when_there_is_no_card(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Exactly one vehicle at home that identifies itself: that is the vehicle."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _set(hass, GLB_TRACKER, "home")
    await _set(hass, EQB_TRACKER, "not_home")

    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "GLB"
    await _unplug(hass, freezer)
    assert (await _stored(hass))[0].identification_source == "vehicle_api"


async def test_a_vehicle_is_not_chosen_because_the_other_one_is_away(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """One vehicle says it is away, the other says nothing: the session stays unassigned."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _set(hass, GLB_TRACKER, "unavailable")
    await _set(hass, EQB_TRACKER, "not_home")

    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "unresolved"


async def test_a_card_and_a_different_vehicle_report_flag_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The card wins, the session is marked as a conflict and flagged."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _set(hass, GLB_TRACKER, "not_home")
    await _set(hass, EQB_TRACKER, "home")
    await _set(hass, CARD, "11223344")

    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)
    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.vehicle_id == "v001"
    assert session.identification_conflict is True
    assert session.status == "flagged"
    assert session.location_conflict is True


async def test_an_unassigned_session_is_resolved_once_one_vehicle_reports_charging(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Later evidence assigns an open session, without the start values."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)
    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "unresolved"

    await _set(hass, GLB_CHARGE, "13")
    await _set(hass, EQB_CHARGE, "3")

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "GLB"
    await _unplug(hass, freezer)
    session = (await _stored(hass))[0]
    assert session.vehicle_id == "v001"
    assert session.identification_source == "vehicle_api"
    assert session.capacity_kwh == 85.0
    assert session.soc_start is None
    assert session.odometer_km is None
    assert "soc_start" in session.open_fields
    assert "odometer_km" in session.open_fields
    assert session.status == "followup_open"


async def test_two_vehicles_reporting_charging_do_not_resolve_a_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Without exactly one candidate nothing is guessed."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _set(hass, GLB_CHARGE, "13")
    await _set(hass, EQB_CHARGE, "13")
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    hass.states.async_set(GLB_CHARGE, "13", {"refreshed": True})
    await hass.async_block_till_done()

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "unresolved"


async def test_a_vehicle_reporting_charging_before_the_window_ends_does_not_decide_it(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The decision waits for the identification window."""
    await _setup(hass, vehicles=(_glb(),))
    await _start_charging(hass, freezer)

    await _set(hass, GLB_CHARGE, "13")

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "unresolved"


async def test_a_vehicle_already_charging_at_the_decision_resolves_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Exactly one vehicle reporting charging when the window ends is taken as the vehicle."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _start_charging(hass, freezer)
    await _set(hass, GLB_CHARGE, "13")
    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "unresolved"

    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "GLB"


async def test_a_guest_vehicle_is_published_as_guest(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A guest vehicle shows as guest, never by name."""
    guest = Vehicle(
        id="v003",
        name="Visitor",
        is_guest=True,
        cards=(Card(uid="99887766", label="Visitor card"),),
    ).to_dict()
    await _setup(hass, vehicles=(guest,))
    await _set(hass, CARD, "99887766")
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.ev_charging_active_vehicle").state == "guest"


# ------------------------------------------------------------------ persistence


async def test_a_session_survives_a_restart_and_reports_the_gap(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Energy delivered while the integration was not running is measured but unallocated."""
    entry, _ = await _setup(hass)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    freezer.tick(timedelta(minutes=10))
    hass.states.async_set(TOTAL, "101.8", {"unit_of_measurement": "kWh"})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "charging"
    await _advance(hass, freezer, 60)
    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].energy_measured_kwh == pytest.approx(1.8)
    assert sessions[0].energy_unallocated_kwh == pytest.approx(0.8)


async def test_a_session_unplugged_during_a_restart_is_closed(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A restored session ends when the plug state shows it is disconnected."""
    entry, _ = await _setup(hass)
    await _start_charging(hass, freezer)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(PLUG, UNPLUGGED)
    hass.states.async_set(POWER, "0", {"unit_of_measurement": "kW"})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _advance(hass, freezer, 3)

    assert len(await _stored(hass)) == 1
    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "idle"


async def test_the_session_belongs_to_the_year_of_its_local_start(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A session that starts on New Year's Eve and ends after midnight is stored in the old year."""
    freezer.move_to("2026-12-31 22:50:00+00:00")
    await _setup(hass)
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 3600)
    await _unplug(hass, freezer)

    assert len(await _stored(hass, 2026)) == 1
    assert await _stored(hass, 2027) == []


async def test_stored_fields_are_not_altered_by_later_capture(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A second session is added next to the first without changing it."""
    await _setup(hass)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")
    await _unplug(hass, freezer)
    first = (await _stored(hass))[0]

    await _advance(hass, freezer, 3600)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.5", "kWh")
    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 2
    assert sessions[0] == first


# --------------------------------------------------------------------- entities


async def test_no_personal_value_appears_in_an_entity_state(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, caplog: pytest.LogCaptureFixture
) -> None:
    """VIN, card identifier and card label never show up in a state, attribute or info log."""
    caplog.set_level(logging.INFO)
    await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, "11223344")
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    forbidden = ("W1NSYNTHETIC000001", GLB_CARD, "11223344", "Card GLB")
    for state in hass.states.async_all():
        if not state.entity_id.startswith(("sensor.ev_charging", "binary_sensor.ev_charging")):
            continue
        rendered = f"{state.state} {state.attributes}"
        for value in forbidden:
            assert value not in rendered, state.entity_id
    await _unplug(hass, freezer)
    for record in caplog.records:
        if record.name.startswith("custom_components.ev_charging"):
            for value in forbidden:
                assert value not in record.getMessage()


async def test_the_documented_entities_exist(hass: HomeAssistant) -> None:
    """The entities of the wallbox level are created under their documented ids."""
    await _setup(hass)

    for entity_id in (
        "binary_sensor.ev_charging_wallbox_session",
        "sensor.ev_charging_wallbox_state",
        "sensor.ev_charging_active_vehicle",
        "sensor.ev_charging_session_cost",
        "sensor.ev_charging_session_energy_grid",
        "sensor.ev_charging_session_energy_solar",
        "sensor.ev_charging_price_effective",
        "sensor.ev_charging_open_followups",
    ):
        assert hass.states.get(entity_id) is not None, entity_id


async def test_the_resolving_entities_are_disabled_by_default(hass: HomeAssistant) -> None:
    """Entities that only restate resolved values are created but not enabled."""
    from homeassistant.helpers import entity_registry as er

    await _setup(hass)
    registry = er.async_get(hass)

    for entity_id in (
        "sensor.ev_charging_active_vehicle_soc",
        "sensor.ev_charging_active_vehicle_soc_target",
        "sensor.ev_charging_active_vehicle_charge_state",
        "sensor.ev_charging_active_vehicle_charge_end",
        "sensor.ev_charging_session_soc_start",
        "sensor.ev_charging_session_odometer_start",
        "sensor.ev_charging_session_duration_net",
        "sensor.ev_charging_grid_share",
    ):
        entry = registry.async_get(entity_id)
        assert entry is not None, entity_id
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION, entity_id
        assert hass.states.get(entity_id) is None, entity_id


async def test_session_values_are_published_on_the_interval(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Numeric values are refreshed at the publish interval, not with every counter step."""
    await _setup(hass, hub=_hub(update_interval_s=60))
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")
    published = hass.states.get("sensor.ev_charging_session_cost").state

    await _set(hass, TOTAL, "101.1", "kWh")
    assert hass.states.get("sensor.ev_charging_session_cost").state == published

    await _advance(hass, freezer, 61)
    assert hass.states.get("sensor.ev_charging_session_cost").state != published


async def test_open_followups_counts_the_stored_sessions_that_wait(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """An unassigned session is an open follow-up."""
    await _setup(hass)
    assert hass.states.get("sensor.ev_charging_open_followups").state == "0"
    await _touch_year_file(hass, 2026)

    await _start_charging(hass, freezer)
    await _unplug(hass, freezer)
    await _advance(hass, freezer, 31)

    assert hass.states.get("sensor.ev_charging_open_followups").state == "1"


async def test_the_live_payload_does_not_carry_personal_values(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The live values for the card carry no card, VIN, address or coordinates."""
    _, manager = await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, "11223344")
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    payload = manager.live_payload()

    rendered = str(payload)
    for value in ("W1NSYNTHETIC000001", GLB_CARD, "11223344", "Card GLB"):
        assert value not in rendered
    assert payload["vehicle"] == {"id": "v001", "name": "GLB"}
    assert payload["state"] == "charging"
    assert payload["charge_power_kw"] == 7.0


# --------------------------------------------------------------------- live card


async def test_live_subscription_sends_the_state_now_and_after_a_change(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, freezer: FrozenDateTimeFactory
) -> None:
    """The card receives the present values at once and again when a source changes."""
    await _setup(hass)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "ev_charging/live/subscribe"})
    assert (await client.receive_json())["success"]
    first = await client.receive_json()
    assert first["event"]["state"] == "idle"
    assert first["event"]["active"] is False

    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 2)

    candidate = await client.receive_json()
    charging = await client.receive_json()
    assert candidate["event"]["state"] == "candidate"
    assert charging["event"]["state"] == "charging"
    assert charging["event"]["charge_power_kw"] == 6.0


async def test_live_subscription_needs_no_administrator(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_read_only_access_token: str
) -> None:
    """Reading the live values needs a signed-in user only."""
    await _setup(hass)
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json_auto_id({"type": "ev_charging/live/subscribe"})

    assert (await client.receive_json())["success"]


async def test_live_subscription_without_a_wallbox_is_an_error(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Without a wallbox there is nothing to show."""
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data=_hub(), version=4, minor_version=1)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "ev_charging/live/subscribe"})

    response = await client.receive_json()
    assert response["success"] is False
    assert response["error"]["code"] == "not_found"


async def test_a_source_that_changes_its_unit_is_not_read_and_raises_an_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A power sensor that starts reporting watts is never converted silently."""
    entry, _ = await _setup(hass)
    await _set(hass, PLUG, PLUGGED)

    await _set(hass, POWER, "7000", "W")

    assert hass.states.get("sensor.ev_charging_wallbox_state").state == "idle"
    issue_id = problems.role_unit_changed_issue_id(_wallbox_subentry_id(entry), "charge_power")
    assert _issue(hass, issue_id) is not None
