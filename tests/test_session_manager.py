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
    LOCATION_EXTERNAL,
    LOCATION_HOME_NO_WALLBOX,
    SESSION_STATE_CHARGING,
    SESSION_STATE_ERROR,
    SESSION_STATUS_FLAGGED,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
    store_key_sessions,
)
from custom_components.ev_charging.models import Card, EntityRole, HubSettings, Vehicle, Wallbox
from custom_components.ev_charging.session_manager import (
    LateIdentification,
    SessionManager,
    StepKind,
    counter_step,
    energy_raw_kwh,
    identify,
    identify_late,
    is_wallbox_vehicle,
    should_discard,
)
from custom_components.ev_charging.store import SessionYearStore
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from tests.fake_modbus import NO_CONNECTION, OK, FakeDevice, install, registers_for

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
GLB_END = "sensor.glb_charge_end"
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
    plug: str = UNPLUGGED,
) -> tuple[MockConfigEntry, SessionManager]:
    """Set up the integration with a wallbox and vehicles, all sources idle."""
    if start_states:
        hass.states.async_set(PLUG, plug)
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
        version=5,
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


def test_identify_by_the_start_of_a_card() -> None:
    """The wallbox may report the start of the serial number instead of its end."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"))

    result = identify("AABBCCDD", [glb], set())

    assert (result.source, result.vehicle_id, result.card_uid) == ("rfid", "v001", GLB_CARD)


def test_identify_ignores_the_middle_of_a_card() -> None:
    """A value that is neither the start nor the end of a card is no match."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"))

    result = identify("BBCCDD11", [glb], set())

    assert result.vehicle_id is None
    assert result.unknown_card is True


def test_identify_a_card_that_matches_at_both_ends_is_one_match() -> None:
    """The same card at the start and at the end of the value is not ambiguous."""
    vehicle = _vehicle("v001", Card(uid="AABB1122AABB", label="a"))

    result = identify("AABB", [vehicle], set())

    assert result.vehicle_id == "v001"
    assert result.unknown_card is False


def test_identify_a_value_that_starts_one_card_and_ends_another_is_no_match() -> None:
    """Two cards fit, one at its start and one at its end: nothing is guessed."""
    first = _vehicle("v001", Card(uid="11223344AAAA", label="a"))
    second = _vehicle("v002", Card(uid="BBBB11223344", label="b"))

    result = identify("11223344", [first, second], set())

    assert result.vehicle_id is None
    assert result.unknown_card is False
    assert result.card_uid == "11223344"


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


def _late(
    card: str,
    vehicles: list[Vehicle],
    *,
    vehicle_id: str | None = None,
    source: str = "unresolved",
) -> LateIdentification:
    return identify_late(card, vehicles, vehicle_id=vehicle_id, source=source)


def test_a_late_card_assigns_an_unassigned_session_to_its_vehicle() -> None:
    """The vehicle of the card is taken, and the source follows the type of the card."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="Card GLB", type="emaid"))

    result = _late(GLB_CARD, [glb])

    assert (result.vehicle_id, result.source) == ("v001", "emaid")
    assert result.card_uid == GLB_CARD
    assert result.card_label == "Card GLB"
    assert result.conflict is False
    assert result.unknown_card is False


def test_a_late_card_is_matched_by_the_start_of_the_stored_card() -> None:
    """The wallbox reports the start of the printed serial number."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"))

    result = _late("AABBCCDD", [glb])

    assert result.vehicle_id == "v001"
    assert result.card_uid == GLB_CARD


def test_a_late_card_is_matched_by_the_end_of_the_stored_card() -> None:
    """The wallbox reports only the end of the printed serial number."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"))

    assert _late("11223344", [glb]).vehicle_id == "v001"


def test_a_late_card_of_the_vehicle_already_assigned_changes_only_the_source() -> None:
    """The vehicle report and the card agree: no conflict, and the source is now the card."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"), api=True)

    result = _late(GLB_CARD, [glb], vehicle_id="v001", source="vehicle_api")

    assert (result.vehicle_id, result.source) == ("v001", "rfid")
    assert result.conflict is False


def test_a_late_card_of_another_vehicle_wins_and_is_a_conflict() -> None:
    """The card names a vehicle other than the one the vehicle report chose."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"), api=True)
    eqb = _vehicle("v002", Card(uid=EQB_CARD, label="b"), api=True)

    result = _late(EQB_CARD, [glb, eqb], vehicle_id="v001", source="vehicle_api")

    assert (result.vehicle_id, result.source) == ("v002", "rfid")
    assert result.conflict is True


def test_a_late_unknown_card_leaves_an_unassigned_session_unassigned() -> None:
    """A card nobody holds is kept and reported, and does not assign anything."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"), api=True)

    result = _late("DEADBEEF", [glb])

    assert result.vehicle_id is None
    assert result.source == "unresolved"
    assert result.card_uid == "DEADBEEF"
    assert result.unknown_card is True
    assert result.conflict is False


def test_a_late_unknown_card_is_a_conflict_for_a_session_the_vehicle_report_assigned() -> None:
    """The vehicle stays, and the disagreement is recorded."""
    glb = _vehicle("v001", Card(uid=GLB_CARD, label="a"), api=True)

    result = _late("DEADBEEF", [glb], vehicle_id="v001", source="vehicle_api")

    assert (result.vehicle_id, result.source) == ("v001", "vehicle_api")
    assert result.unknown_card is True
    assert result.conflict is True


def test_a_late_ending_that_fits_two_cards_changes_nothing() -> None:
    """An ambiguous ending is no match: no vehicle is chosen, and nothing is a conflict."""
    first = _vehicle("v001", Card(uid="AAAA11223344", label="a"))
    second = _vehicle("v002", Card(uid="BBBB11223344", label="b"))

    unassigned = _late("11223344", [first, second])
    assigned = _late("11223344", [first, second], vehicle_id="v001", source="vehicle_api")

    assert (unassigned.vehicle_id, unassigned.source) == (None, "unresolved")
    assert (assigned.vehicle_id, assigned.source) == ("v001", "vehicle_api")
    for result in (unassigned, assigned):
        assert result.unknown_card is False
        assert result.conflict is False


_NOTHING = {
    "ended_by_unplug": True,
    "counter_readable": True,
    "counter_increased": False,
    "phase_begun": False,
    "charge_error": False,
    "flagged": False,
    "identification_conflict": False,
}


def test_a_session_without_content_that_ended_by_unplugging_is_discarded() -> None:
    """Readable counter that did not rise, no phase, no error, no marking: nothing is kept."""
    assert should_discard(**_NOTHING) is True


@pytest.mark.parametrize(
    "content",
    ["counter_increased", "phase_begun", "charge_error", "flagged", "identification_conflict"],
)
def test_a_session_with_any_content_is_kept(content: str) -> None:
    """Any one sign that something happened keeps the session."""
    assert should_discard(**{**_NOTHING, content: True}) is False


def test_a_session_is_kept_when_the_counter_was_not_readable() -> None:
    """Without certainty that no energy flowed, the session stays."""
    assert should_discard(**{**_NOTHING, "counter_readable": False}) is False


def test_a_session_that_did_not_end_by_unplugging_is_never_discarded() -> None:
    """Ending by the timeout is never a reason to drop a session."""
    assert should_discard(**{**_NOTHING, "ended_by_unplug": False}) is False


# ------------------------------------------------------------------ candidate


async def test_candidate_is_published_at_once(hass: HomeAssistant) -> None:
    """The candidate state and the session flag appear the moment the plug reports a vehicle."""
    await _setup(hass)

    await _set(hass, PLUG, PLUGGED)

    assert hass.states.get("sensor.carport_wallbox_state").state == "candidate"
    assert hass.states.get("binary_sensor.carport_wallbox_session").state == "on"


async def test_candidate_becomes_a_session_after_the_debounce(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The candidate turns into a running session once the debounce time has passed."""
    await _setup(hass)

    await _start_charging(hass, freezer)

    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"


async def test_a_plugged_vehicle_without_power_is_a_paused_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The session begins with the plug, waits without a phase, and the first power starts one."""
    _, manager = await _setup(hass)
    plugged_at = dt_util.utcnow()
    await _set(hass, PLUG, PLUGGED)

    await _advance(hass, freezer, 2)

    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"
    assert hass.states.get("binary_sensor.carport_wallbox_session").state == "on"
    payload = manager.live_payload()
    assert payload["phase_count"] == 0
    assert payload["waiting_for_power"] is True

    await _advance(hass, freezer, 3600)
    await _set(hass, POWER, "7.0", "kW")
    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
    assert manager.live_payload()["waiting_for_power"] is False
    await _advance(hass, freezer, 600)
    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    session = sessions[0]
    plug_start = dt_util.parse_datetime(session.plug_start)
    assert abs((plug_start - plugged_at).total_seconds()) < 1
    assert session.phase_count == 1
    first_phase = dt_util.parse_datetime(session.phases[0].start)
    assert (first_phase - plug_start).total_seconds() == pytest.approx(3602, abs=2)
    assert session.pause_duration_min == pytest.approx(60.0, abs=0.5)
    assert session.charge_duration_min == pytest.approx(10.0, abs=0.2)


async def test_the_first_phase_starts_when_the_power_first_exceeded_the_threshold(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Power that rises within the debounce time dates the phase from that moment."""
    await _setup(hass)
    plugged_at = dt_util.utcnow()
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 1)
    powered_at = dt_util.utcnow()
    await _set(hass, POWER, "7.0", "kW")

    await _advance(hass, freezer, 1)
    await _advance(hass, freezer, 600)
    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert abs((dt_util.parse_datetime(session.plug_start) - plugged_at).total_seconds()) < 1
    assert abs((dt_util.parse_datetime(session.phases[0].start) - powered_at).total_seconds()) < 1


async def test_a_flicker_of_the_plug_below_the_debounce_makes_no_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A connector report that does not last leaves no session behind."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 1)

    await _set(hass, PLUG, UNPLUGGED)
    await _advance(hass, freezer, 60)

    assert hass.states.get("sensor.carport_wallbox_state").state == "idle"
    assert hass.states.get("binary_sensor.carport_wallbox_session").state == "off"
    assert await _stored(hass) == []


async def test_power_starts_a_candidate_while_the_connector_reports_nothing(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Without a connector report, power above the threshold begins the session instead."""
    await _setup(hass, plug="undefined")

    await _set(hass, POWER, "7.0", "kW")
    assert hass.states.get("sensor.carport_wallbox_state").state == "candidate"
    await _advance(hass, freezer, 2)

    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"


async def test_a_candidate_started_by_power_is_dropped_when_the_power_falls_back(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A brief peak without a connector report leaves no session behind."""
    await _setup(hass, plug="undefined")
    await _set(hass, POWER, "7.0", "kW")

    await _set(hass, POWER, "0.1", "kW")
    await _advance(hass, freezer, 5)

    assert hass.states.get("sensor.carport_wallbox_state").state == "idle"
    assert hass.states.get("binary_sensor.carport_wallbox_session").state == "off"
    assert await _stored(hass) == []


async def test_a_candidate_started_by_the_plug_does_not_depend_on_the_power(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The plug made the candidate, so power that comes and goes does not drop it."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _set(hass, POWER, "7.0", "kW")

    await _set(hass, POWER, "0.1", "kW")
    await _advance(hass, freezer, 5)

    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"


async def test_a_zero_debounce_confirms_immediately(hass: HomeAssistant) -> None:
    """Without a debounce time the session runs right away."""
    await _setup(hass, wallbox=_wallbox(start_debounce_s=0))

    await _set(hass, PLUG, PLUGGED)
    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"

    await _set(hass, POWER, "7.0", "kW")
    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"


async def test_no_candidate_while_the_connector_reports_not_connected(
    hass: HomeAssistant,
) -> None:
    """Power alone does not start a session while the wallbox says nothing is plugged in."""
    await _setup(hass)

    await _set(hass, POWER, "7.0", "kW")

    assert hass.states.get("sensor.carport_wallbox_state").state == "idle"


async def test_a_vehicle_plugged_in_at_startup_begins_a_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """With no stored session, a vehicle that is already plugged in begins one at that moment."""
    await _setup(hass, plug=PLUGGED)

    assert hass.states.get("sensor.carport_wallbox_state").state == "candidate"
    await _advance(hass, freezer, 2)

    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"
    assert hass.states.get("binary_sensor.carport_wallbox_session").state == "on"


async def test_the_next_session_begins_at_once_when_the_vehicle_is_still_plugged_in(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """After a session is stored the plug and power are looked at again."""
    await _setup(hass)
    await _start_charging(hass, freezer)
    await _set(hass, POWER, "0", "kW")
    await _set(hass, PLUG, UNPLUGGED)
    await _advance(hass, freezer, 1)
    await _set(hass, PLUG, PLUGGED)

    await _advance(hass, freezer, 2)

    assert len(await _stored(hass)) == 1
    assert hass.states.get("sensor.carport_wallbox_state").state == "candidate"
    await _advance(hass, freezer, 2)
    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"


# ---------------------------------------------------------------- one session


async def test_power_dropping_and_rising_again_makes_one_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Below the threshold and back above it, with the plug connected throughout: one session."""
    await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, POWER, "0.0", "kW")
    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"
    await _advance(hass, freezer, 120)
    await _set(hass, POWER, "6.5", "kW")
    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
    await _set(hass, POWER, "0.0", "kW")
    await _advance(hass, freezer, 120)
    await _set(hass, POWER, "5.0", "kW")
    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].phase_count == 1


async def test_power_rising_in_a_plugged_session_never_makes_a_second_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A vehicle that waits for power and then charges is one session, not two."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 1800)
    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"

    await _set(hass, POWER, "6.5", "kW")
    await _advance(hass, freezer, 300)
    await _set(hass, POWER, "0.0", "kW")
    await _advance(hass, freezer, 300)
    await _set(hass, POWER, "6.5", "kW")
    await _advance(hass, freezer, 300)
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

    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"
    assert await _stored(hass) == []

    await _unplug(hass, freezer)
    assert len(await _stored(hass)) == 1
    assert hass.states.get("sensor.carport_wallbox_state").state == "idle"


async def test_a_neutral_plug_value_keeps_the_session_open_without_a_repair_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A value the mapping marks neutral leaves the last class in force."""
    entry, _ = await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, PLUG, "undefined")
    await _advance(hass, freezer, 60)

    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
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

    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
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

    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
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
    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"


async def test_a_charging_error_does_not_end_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A reported error puts the session in the error state and leaves it open."""
    await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)

    assert hass.states.get("sensor.carport_wallbox_state").state == "error"
    assert await _stored(hass) == []

    await _set(hass, ERROR, "charging")
    await _set(hass, POWER, "6.0", "kW")
    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"

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

    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"


async def test_a_neutral_error_value_keeps_the_error_class(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The neutral value of the error role neither raises nor clears an error."""
    await _setup(hass)
    await _start_charging(hass, freezer)
    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)

    await _set(hass, ERROR, "undefined")

    assert hass.states.get("sensor.carport_wallbox_state").state == "error"


# -------------------------------------------------------------------- discarding


async def _year_file_exists(hass: HomeAssistant, year: int = 2026) -> bool:
    def _exists() -> bool:
        return os.path.exists(hass.config.path(".storage", store_key_sessions(year)))

    return await hass.async_add_executor_job(_exists)


async def test_a_plugged_vehicle_that_never_charges_leaves_no_record(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Plugged in for half an hour without power, then unplugged: no session is kept."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 1800)
    assert hass.states.get("binary_sensor.carport_wallbox_session").state == "on"

    await _unplug(hass, freezer)

    assert await _stored(hass) == []
    assert not await _year_file_exists(hass)
    assert hass.states.get("sensor.carport_wallbox_state").state == "idle"
    assert hass.states.get("binary_sensor.carport_wallbox_session").state == "off"


async def test_a_session_that_is_discarded_does_not_touch_the_stored_sessions(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Sessions kept earlier stay exactly as they were, and their count is not asked again."""
    await _setup(hass)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")
    await _unplug(hass, freezer)
    first = await _stored(hass)
    assert len(first) == 1

    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 1800)
    await _unplug(hass, freezer)

    assert await _stored(hass) == first


async def test_a_counter_rise_without_a_phase_keeps_the_session_and_books_it_on_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Energy that flows below the power threshold is kept, without a phase being invented."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _set(hass, POWER, "0.3", "kW")
    await _advance(hass, freezer, 60)

    await _set(hass, TOTAL, "100.1", "kWh")
    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    session = sessions[0]
    assert session.phase_count == 0
    assert session.phases == ()
    assert session.charge_duration_min == 0
    assert session.power_avg_kw is None
    assert session.energy_measured_kwh == pytest.approx(0.1)
    assert session.energy_grid_kwh == pytest.approx(0.0)
    assert session.energy_solar_kwh == pytest.approx(0.1)
    assert session.cost == pytest.approx(0.1 * 0.08)


async def test_an_unreadable_counter_keeps_a_session_without_content(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A counter that cannot be read at the end leaves no certainty that nothing flowed."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 60)
    await _set(hass, TOTAL, "unavailable")

    await _unplug(hass, freezer)

    assert len(await _stored(hass)) == 1


async def test_a_counter_that_was_unreadable_at_the_start_keeps_a_session_without_content(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Energy that may have flowed before the counter was first read leaves no certainty."""
    await _setup(hass)
    await _set(hass, TOTAL, "unavailable")
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 60)
    await _set(hass, TOTAL, "100.0", "kWh")

    await _unplug(hass, freezer)

    assert len(await _stored(hass)) == 1


async def test_a_reported_charging_error_keeps_a_session_without_a_phase(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A charging error was reported, so there is something to look at."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 2)
    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)
    assert hass.states.get("sensor.carport_wallbox_state").state == "error"

    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].charge_error is True
    assert sessions[0].phase_count == 0


async def test_a_flagged_session_is_kept_even_without_energy_or_a_phase(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A counter jump that is not accumulated still flags the session, and that keeps it."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "1000.0", "kWh")

    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].status == "flagged"
    assert sessions[0].energy_measured_kwh == 0.0


async def test_an_identification_conflict_keeps_a_session_without_a_phase(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The card and the vehicle report disagree, which is marked and therefore kept."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _set(hass, GLB_TRACKER, "not_home")
    await _set(hass, EQB_TRACKER, "home")
    await _set(hass, CARD, "11223344")
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 20)

    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].identification_conflict is True
    assert sessions[0].phase_count == 0


async def test_a_session_closed_by_the_timeout_is_never_discarded(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """When the source is lost for good the session is closed and kept, empty or not."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 2)
    await _set(hass, PLUG, "unavailable")

    await _advance(hass, freezer, 12 * 3600 + 5)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].status == "flagged"
    assert sessions[0].phase_count == 0


async def test_the_repair_issue_for_an_unknown_card_stays_when_the_session_is_discarded(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The unknown card was seen, whatever became of the session."""
    entry, _ = await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, "DEADBEEF")
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 20)
    issue_id = problems.unknown_card_issue_id(_wallbox_subentry_id(entry))
    assert _issue(hass, issue_id) is not None

    await _unplug(hass, freezer)

    assert await _stored(hass) == []
    assert _issue(hass, issue_id) is not None


async def test_the_open_followup_count_is_not_asked_again_for_a_discarded_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A discarded session makes no read of the stored sessions."""
    _, manager = await _setup(hass)
    calls: list[int] = []
    original = manager._async_count_followups

    async def _counting() -> int:
        calls.append(1)
        return await original()

    monkeypatch.setattr(manager, "_async_count_followups", _counting)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 60)

    await _unplug(hass, freezer)

    assert calls == []


# --------------------------------------------------------------------- live state


async def test_the_live_payload_says_what_the_state_is_and_since_when(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """State, its start, the phases so far, the plug and whether the session waits for power."""
    _, manager = await _setup(hass)
    idle = manager.live_payload()
    assert idle["active"] is False
    assert idle["state_since"] is None
    assert idle["phase_count"] == 0
    assert idle["plug"] == {"state": "not_connected", "unavailable_since": None, "timeout_at": None}

    plugged_at = dt_util.utcnow()
    await _set(hass, PLUG, PLUGGED)
    candidate = manager.live_payload()
    assert candidate["state"] == "candidate"
    assert candidate["plug"]["state"] == "connected"
    assert abs((dt_util.parse_datetime(candidate["state_since"]) - plugged_at).total_seconds()) < 1

    await _advance(hass, freezer, 2)
    waiting = manager.live_payload()
    assert waiting["state"] == "paused"
    assert waiting["waiting_for_power"] is True
    assert waiting["phase_count"] == 0
    waiting_since = dt_util.parse_datetime(waiting["state_since"])
    assert (waiting_since - plugged_at).total_seconds() == pytest.approx(2, abs=1)

    await _advance(hass, freezer, 600)
    await _set(hass, POWER, "7.0", "kW")
    charging = manager.live_payload()
    assert charging["state"] == "charging"
    assert charging["waiting_for_power"] is False
    assert charging["phase_count"] == 1
    assert (dt_util.parse_datetime(charging["state_since"]) - waiting_since).total_seconds() == (
        pytest.approx(600, abs=1)
    )

    await _advance(hass, freezer, 60)
    await _set(hass, POWER, "0.0", "kW")
    paused = manager.live_payload()
    assert paused["state"] == "paused"
    assert paused["waiting_for_power"] is False
    assert paused["phase_count"] == 1


async def test_the_live_payload_reports_the_state_of_the_plug_with_or_without_a_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Not connected, connected, and not usable, and how long the session may wait for it."""
    _, manager = await _setup(hass)
    assert manager.live_payload()["plug"]["state"] == "not_connected"

    await _set(hass, PLUG, "unavailable")
    without_session = manager.live_payload()
    assert without_session["plug"] == {
        "state": "unavailable",
        "unavailable_since": None,
        "timeout_at": None,
    }

    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 2)
    assert manager.live_payload()["plug"]["state"] == "connected"

    lost_at = dt_util.utcnow()
    await _set(hass, PLUG, "unavailable")
    plug = manager.live_payload()["plug"]
    assert plug["state"] == "unavailable"
    assert abs((dt_util.parse_datetime(plug["unavailable_since"]) - lost_at).total_seconds()) < 1
    timeout_at = dt_util.parse_datetime(plug["timeout_at"])
    assert (timeout_at - dt_util.parse_datetime(plug["unavailable_since"])).total_seconds() == (
        12 * 3600
    )

    await _set(hass, PLUG, PLUGGED)
    assert manager.live_payload()["plug"] == {
        "state": "connected",
        "unavailable_since": None,
        "timeout_at": None,
    }


async def test_the_live_payload_separates_the_identification_conflict_from_the_marking(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The conflict is reported by itself, and a marking alone is no conflict."""
    _, manager = await _setup(hass, vehicles=(_glb(), _eqb()))
    await _set(hass, GLB_TRACKER, "not_home")
    await _set(hass, EQB_TRACKER, "home")
    await _set(hass, CARD, "11223344")
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 20)

    payload = manager.live_payload()

    assert payload["identification_decided"] is True
    assert payload["identification_conflict"] is True
    assert payload["flagged"] is True

    await _unplug(hass, freezer)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _set(hass, TOTAL, "5000.0", "kWh")
    payload = manager.live_payload()
    assert payload["identification_conflict"] is False
    assert payload["flagged"] is True


async def test_the_live_payload_reports_the_energy_counter_and_whether_it_changed(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The counter that carries the energy, and that it is not the one that was set up."""
    _, manager = await _setup(hass, wallbox=_both_counters())
    assert manager.live_payload()["counter"] == {"authoritative": None, "switched": False}
    await _start_charging(hass, freezer, power_kw=6.0)
    assert manager.live_payload()["counter"] == {"authoritative": "total", "switched": False}

    for step in (1, 2, 3):
        await _advance(hass, freezer, 60)
        await _set(hass, SESSION, f"{step / 10}", "kWh")
    await _advance(hass, freezer, 60)

    payload = manager.live_payload()
    assert payload["counter"] == {"authoritative": "session", "switched": True}
    assert payload["energy_unallocated_kwh"] == pytest.approx(0.2)


async def test_the_live_payload_says_which_sources_are_missing_for_the_split_and_the_cost(
    hass: HomeAssistant,
) -> None:
    """Without a grid balance no split, without a grid price no cost."""
    _, complete = await _setup(hass)
    assert complete.live_payload()["sources"] == {"grid_balance": True, "grid_price": True}
    assert complete.live_payload()["energy_unallocated_kwh"] is None
    await hass.config_entries.async_unload(complete._entry.entry_id)

    _, bare = await _setup(
        hass, hub=_hub(grid_power=None, price_grid_fixed=None, price_feed_in_fixed=None)
    )

    assert bare.live_payload()["sources"] == {"grid_balance": False, "grid_price": False}


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


async def test_a_short_grid_spike_is_smoothed_over_the_window(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Ten seconds of grid import weigh in with their share of the last 60 seconds only."""
    await _setup(hass)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 120)

    await _set(hass, GRID, "3000", "W")
    await _advance(hass, freezer, 5)
    await _set(hass, TOTAL, "100.1", "kWh")
    await _advance(hass, freezer, 5)
    await _set(hass, GRID, "0", "W")
    await _advance(hass, freezer, 5)
    await _set(hass, TOTAL, "100.2", "kWh")
    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.energy_measured_kwh == pytest.approx(0.2)
    # Read unsmoothed, the first increment alone would have been half grid energy (0.05 kWh).
    # The spike of 3 kW for 10 s counts as 250 W and then 500 W over the window of 60 s.
    expected_grid = 0.1 * 0.25 / 6 + 0.1 * 0.5 / 6
    assert session.energy_grid_kwh == pytest.approx(expected_grid, abs=6e-4)
    assert session.energy_grid_kwh < 0.02
    assert session.energy_grid_kwh + session.energy_solar_kwh == pytest.approx(0.2, abs=2e-3)


async def test_a_grid_balance_that_swings_every_second_gives_a_steady_share(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A sensor that reports every second and swings between 0 and 2 kW does not skew an increment.

    The counter increments arrive alternately right after the balance jumped up and right after
    it jumped down. Each is valued with the share of the last 60 seconds, one sixth of 6 kW,
    and not with the value of the moment.
    """
    _, manager = await _setup(hass)
    await _start_charging(hass, freezer, power_kw=6.0)
    shares: list[float] = []
    total = 100.0

    for step in range(120):
        await _set(hass, GRID, "2000" if step % 2 == 0 else "0", "W")
        if step % 5 == 0 and step >= 60:
            total += 0.02
            await _set(hass, TOTAL, f"{total:.3f}", "kWh")
            shares.append(manager.live_payload()["grid_share_pct"])
        await _advance(hass, freezer, 1)

    assert len(shares) == 12
    high_moment = shares[0::2]
    low_moment = shares[1::2]
    for share in shares:
        assert share == pytest.approx(100 / 6, abs=0.5)
    assert max(high_moment) - min(low_moment) < 1.0


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
    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"

    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
    await _unplug(hass, freezer)
    session = (await _stored(hass))[0]
    assert session.vehicle_id == "v001"
    assert session.vehicle_name == "GLB"
    assert session.identification_source == "rfid"
    assert session.card_uid == GLB_CARD
    assert session.card_label == "Card GLB"
    assert session.id.endswith("_v001")


async def test_a_card_reported_as_its_start_identifies_the_vehicle(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The start of the serial number is enough, as its end is."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _set(hass, CARD, "AABBCCDD")
    await _start_charging(hass, freezer)

    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"


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

    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"


async def test_an_empty_card_value_is_no_card(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The values 0, unknown and unavailable never count as a card."""
    entry, _ = await _setup(hass, vehicles=(_glb(),))
    for value in ("0", "unknown", "unavailable", ""):
        await _set(hass, CARD, value)
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"
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

    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
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

    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"


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
    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"

    await _set(hass, GLB_CHARGE, "13")
    await _set(hass, EQB_CHARGE, "3")

    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
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

    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"


async def test_a_vehicle_reporting_charging_before_the_window_ends_does_not_decide_it(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The decision waits for the identification window."""
    await _setup(hass, vehicles=(_glb(),))
    await _start_charging(hass, freezer)

    await _set(hass, GLB_CHARGE, "13")

    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"


async def test_a_vehicle_already_charging_at_the_decision_resolves_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Exactly one vehicle reporting charging when the window ends is taken as the vehicle."""
    await _setup(hass, vehicles=(_glb(), _eqb()))
    await _start_charging(hass, freezer)
    await _set(hass, GLB_CHARGE, "13")
    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"

    await _advance(hass, freezer, 20)

    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"


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

    assert hass.states.get("sensor.carport_active_vehicle").state == "guest"


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

    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
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
    assert hass.states.get("sensor.carport_wallbox_state").state == "idle"


async def test_a_waiting_session_survives_a_restart_and_keeps_when_its_state_began(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A waiting session is continued, with its start and the moment it began waiting."""
    entry, manager = await _setup(hass)
    plugged_at = dt_util.utcnow()
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 2)
    since = manager.live_payload()["state_since"]
    await _advance(hass, freezer, 600)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    payload = entry.runtime_data.manager.live_payload()
    assert payload["state"] == "paused"
    assert payload["waiting_for_power"] is True
    assert payload["state_since"] == since
    await _set(hass, POWER, "7.0", "kW")
    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
    await _advance(hass, freezer, 600)
    await _unplug(hass, freezer)

    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert abs((dt_util.parse_datetime(sessions[0].plug_start) - plugged_at).total_seconds()) < 1
    assert sessions[0].phase_count == 1


async def test_a_candidate_survives_a_restart_and_is_confirmed(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A candidate that was stored is confirmed once the debounce time has passed."""
    entry, _ = await _setup(hass, wallbox=_wallbox(start_debounce_s=30))
    await _set(hass, PLUG, PLUGGED)
    assert hass.states.get("sensor.carport_wallbox_state").state == "candidate"
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.carport_wallbox_state").state == "candidate"
    await _advance(hass, freezer, 30)

    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"


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
        if not state.entity_id.startswith(("sensor.carport", "binary_sensor.carport")):
            continue
        rendered = f"{state.state} {state.attributes}"
        for value in forbidden:
            assert value not in rendered, state.entity_id
    await _unplug(hass, freezer)
    for record in caplog.records:
        if record.name.startswith("custom_components.ev_charging"):
            for value in forbidden:
                assert value not in record.getMessage()


def _devices(hass: HomeAssistant, entry: MockConfigEntry) -> list:
    """Return the devices of the config entry."""
    return dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)


async def test_the_entities_of_the_wallbox_belong_to_its_subentry_without_a_device(
    hass: HomeAssistant,
) -> None:
    """The entities hang on the subentry of the wallbox, not on a device, and carry its name."""
    from custom_components.ev_charging.sensor import SENSORS
    from homeassistant.helpers import entity_registry as er

    entry, _ = await _setup(hass, wallbox=_wallbox(manufacturer="KEBA", model="KeContact P40"))
    subentry_id = _wallbox_subentry_id(entry)

    assert _devices(hass, entry) == []
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert len(entities) == len(SENSORS) + 1
    for entity in entities:
        assert entity.device_id is None, entity.entity_id
        assert entity.config_subentry_id == subentry_id, entity.entity_id
        assert entity.entity_id.split(".")[1].startswith("carport_"), entity.entity_id
        assert entity.original_name.startswith("Carport "), entity.entity_id
    state = hass.states.get("sensor.carport_wallbox_state")
    assert state is not None
    assert state.attributes["friendly_name"] == "Carport Wallbox state"


async def test_entities_of_an_earlier_version_lose_their_device_and_keep_their_ids(
    hass: HomeAssistant,
) -> None:
    """Entities on the device of the hub or of the wallbox are detached, nothing else changes."""
    from homeassistant.helpers import entity_registry as er

    hass.states.async_set(PLUG, UNPLUGGED)
    hass.states.async_set(POWER, "0", {"unit_of_measurement": "kW"})
    hass.states.async_set(TOTAL, "100.0", {"unit_of_measurement": "kWh"})
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=_hub(),
        version=5,
        minor_version=1,
        subentries_data=[_subentry(SUBENTRY_TYPE_WALLBOX, _wallbox())],
    )
    entry.add_to_hass(hass)
    hub_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=TITLE,
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    wallbox_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        config_subentry_id=_wallbox_subentry_id(entry),
        identifiers={(DOMAIN, f"{entry.entry_id}_wb001")},
        name="Carport",
    )
    registry = er.async_get(hass)
    legacy = {
        ("sensor", "wallbox_state"): (None, "ev_charging_wallbox_state", hub_device),
        ("sensor", "active_vehicle_soc"): (
            er.RegistryEntryDisabler.INTEGRATION,
            "ev_charging_active_vehicle_soc",
            hub_device,
        ),
        ("sensor", "session_cost"): (None, "carport_session_cost", wallbox_device),
        ("binary_sensor", "wallbox_session"): (None, "carport_wallbox_session", wallbox_device),
    }
    before = {}
    for (domain, key), (disabled_by, object_id, device) in legacy.items():
        registered = registry.async_get_or_create(
            domain,
            DOMAIN,
            f"{entry.entry_id}_{key}",
            config_entry=entry,
            device_id=device.id,
            disabled_by=disabled_by,
            suggested_object_id=object_id,
        )
        before[(domain, key)] = registered.entity_id

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    subentry_id = _wallbox_subentry_id(entry)
    for (domain, key), (disabled_by, object_id, _) in legacy.items():
        detached = registry.async_get(before[(domain, key)])
        assert detached is not None
        assert detached.entity_id == f"{domain}.{object_id}"
        assert detached.unique_id == f"{entry.entry_id}_{key}"
        assert detached.device_id is None
        assert detached.config_subentry_id == subentry_id
        assert detached.disabled_by == disabled_by
    assert hass.states.get("sensor.ev_charging_wallbox_state") is not None
    assert hass.states.get("sensor.ev_charging_active_vehicle_soc") is None
    assert _devices(hass, entry) == []


async def test_the_names_of_the_entities_follow_the_name_of_the_wallbox(
    hass: HomeAssistant,
) -> None:
    """A renamed wallbox renames its entities, and their ids stay."""
    from homeassistant.helpers import entity_registry as er

    entry, _ = await _setup(hass)
    registry = er.async_get(hass)
    entity_id = "sensor.carport_wallbox_state"
    assert registry.async_get(entity_id) is not None
    subentry = next(iter(entry.subentries.values()))

    hass.config_entries.async_update_subentry(
        entry, subentry, data={**subentry.data, "name": "Garage"}, title="Garage"
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    renamed = registry.async_get(entity_id)
    assert renamed is not None
    assert renamed.original_name == "Garage Wallbox state"
    assert hass.states.get(entity_id).attributes["friendly_name"] == "Garage Wallbox state"


async def test_removing_the_wallbox_takes_its_entities_with_it(
    hass: HomeAssistant,
) -> None:
    """Nothing of the wallbox is left when its subentry is removed."""
    from homeassistant.helpers import entity_registry as er

    entry, _ = await _setup(hass)
    subentry_id = _wallbox_subentry_id(entry)
    registry = er.async_get(hass)
    assert [
        entity
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
        if entity.config_subentry_id == subentry_id
    ]

    hass.config_entries.async_remove_subentry(entry, subentry_id)
    await hass.async_block_till_done()

    assert _devices(hass, entry) == []
    assert [
        entity
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
        if entity.config_subentry_id == subentry_id
    ] == []


async def test_the_documented_entities_exist(hass: HomeAssistant) -> None:
    """The entities of the wallbox level are created under their documented ids."""
    await _setup(hass)

    for entity_id in (
        "binary_sensor.carport_wallbox_session",
        "sensor.carport_wallbox_state",
        "sensor.carport_active_vehicle",
        "sensor.carport_session_cost",
        "sensor.carport_session_energy_grid",
        "sensor.carport_session_energy_solar",
        "sensor.carport_price_effective",
        "sensor.carport_open_followups",
    ):
        assert hass.states.get(entity_id) is not None, entity_id


async def test_the_resolving_entities_are_disabled_by_default(hass: HomeAssistant) -> None:
    """Entities that only restate resolved values are created but not enabled."""
    from homeassistant.helpers import entity_registry as er

    await _setup(hass)
    registry = er.async_get(hass)

    for entity_id in (
        "sensor.carport_active_vehicle_soc",
        "sensor.carport_active_vehicle_soc_target",
        "sensor.carport_active_vehicle_charge_state",
        "sensor.carport_active_vehicle_charge_end",
        "sensor.carport_session_soc_start",
        "sensor.carport_session_odometer_start",
        "sensor.carport_session_duration_net",
        "sensor.carport_grid_share",
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
    published = hass.states.get("sensor.carport_session_cost").state

    await _set(hass, TOTAL, "101.1", "kWh")
    assert hass.states.get("sensor.carport_session_cost").state == published

    await _advance(hass, freezer, 61)
    assert hass.states.get("sensor.carport_session_cost").state != published


async def test_open_followups_counts_the_stored_sessions_that_wait(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """An unassigned session is an open follow-up."""
    await _setup(hass)
    assert hass.states.get("sensor.carport_open_followups").state == "0"
    await _touch_year_file(hass, 2026)

    await _start_charging(hass, freezer)
    await _unplug(hass, freezer)
    await _advance(hass, freezer, 31)

    assert hass.states.get("sensor.carport_open_followups").state == "1"


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


async def test_the_live_payload_carries_the_odometer_and_soc_taken_at_the_start(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The start values stay the ones of the start, the state of charge is the present one."""
    _, manager = await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, "11223344")
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)
    await _set(hass, GLB_SOC, "55", "%")
    await _set(hass, GLB_ODO, "7800", "km")

    payload = manager.live_payload()

    assert payload["soc_start"] == 40
    assert payload["soc"] == 55
    assert payload["odometer_km"] == 7699


async def test_the_live_payload_gives_the_charge_end_only_while_the_wallbox_charges(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The vehicle keeps its last expected end; without charging power the card gets the reason."""
    _, manager = await _setup(hass, vehicles=(_glb(charge_end=_role(GLB_END)),))
    hass.states.async_set(GLB_END, "2026-09-20T20:45:00+00:00")
    await _set(hass, CARD, "11223344")
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)

    charging = manager.live_payload()
    assert charging["charge_end"] == "2026-09-20T20:45:00+00:00"
    assert charging["charge_end_missing"] is None

    await _set(hass, POWER, "0", "kW")
    paused = manager.live_payload()
    assert paused["state"] == "paused"
    assert paused["charge_end"] is None
    assert paused["charge_end_missing"] == "no_power"

    await _set(hass, POWER, "7.0", "kW")
    resumed = manager.live_payload()
    assert resumed["charge_end"] == "2026-09-20T20:45:00+00:00"
    assert resumed["charge_end_missing"] is None


async def test_the_live_payload_gives_no_reason_for_a_charge_end_that_is_not_set_up(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A vehicle without a charge end has nothing to explain."""
    _, manager = await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, "11223344")
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)
    await _set(hass, POWER, "0", "kW")

    payload = manager.live_payload()

    assert payload["state"] == "paused"
    assert payload["charge_end"] is None
    assert payload["charge_end_missing"] is None


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
    assert first["event"][0]["state"] == "idle"
    assert first["event"][0]["active"] is False

    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 2)

    candidate = await client.receive_json()
    charging = await client.receive_json()
    assert candidate["event"][0]["state"] == "candidate"
    assert charging["event"][0]["state"] == "charging"
    assert charging["event"][0]["charge_power_kw"] == 6.0


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
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data=_hub(), version=5, minor_version=1)
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
    await _advance(hass, freezer, 2)

    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"
    issue_id = problems.role_unit_changed_issue_id(_wallbox_subentry_id(entry), "charge_power")
    assert _issue(hass, issue_id) is not None


# ------------------------------------------- identification read from the device

DEVICE_HOST = "192.0.2.10"
GLB_REPORTED = "11223344"
EQB_REPORTED = "44556677"
UNKNOWN_REPORTED = "DEADBEEF"
NOTHING_READ = "00000000"


def _register_wallbox(**overrides: Any) -> dict[str, Any]:
    """A wallbox whose identification comes from a register of the device."""
    fields: dict[str, Any] = {
        "identification": None,
        "host": DEVICE_HOST,
        "identification_from_register": True,
    }
    fields.update(overrides)
    return _wallbox(**fields)


def _unreachable() -> tuple[Any, ...]:
    return (NO_CONNECTION,)


def _card(card: str) -> tuple[Any, ...]:
    return (OK, registers_for(card))


async def _setup_with_card(
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    card: str,
    *,
    vehicles: tuple[dict[str, Any], ...],
) -> tuple[MockConfigEntry, FakeDevice | None]:
    """Set up so the wallbox reports the card through an entity or through the register."""
    if source == "register":
        device = install(monkeypatch, FakeDevice([_card(card)]))
        await _setup(hass, wallbox=_register_wallbox(), vehicles=vehicles)
        return _entry(hass), device
    entry, _ = await _setup(hass, vehicles=vehicles)
    await _set(hass, CARD, card)
    return entry, None


def _entry(hass: HomeAssistant) -> MockConfigEntry:
    return hass.config_entries.async_entries(DOMAIN)[0]


def _read_state(manager: SessionManager) -> dict[str, Any] | None:
    return manager.live_payload()["identification_read"]


def _reading(sequence: int, attempt: int, state: str = "reading") -> dict[str, Any]:
    return {"state": state, "sequence": sequence, "attempt": attempt, "max_attempts": 10}


async def _advance_by(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: float, times: int
) -> None:
    """Advance in equal steps: a timer that a step arms is only fired by a later one."""
    for _ in range(times):
        await _advance(hass, freezer, seconds)


def _direct_read_issue(hass: HomeAssistant, entry: MockConfigEntry, issue: str) -> Any:
    return _issue(hass, problems.direct_read_issue_id(issue, _wallbox_subentry_id(entry)))


async def _run_late_card(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    monkeypatch: pytest.MonkeyPatch,
    card: str,
    *,
    vehicles: tuple[dict[str, Any], ...],
    trackers: dict[str, str] | None = None,
) -> tuple[Any, MockConfigEntry]:
    """Plug in, let the cascade decide with nothing read, read the card, unplug, return the record.

    The register holds nothing for the first two reads, at 10 and 15 seconds, and the card at 20.
    """
    install(monkeypatch, FakeDevice([_card(NOTHING_READ), _card(NOTHING_READ), _card(card)]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=vehicles)
    for entity_id, value in (trackers or {}).items():
        await _set(hass, entity_id, value)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 10)
    await _advance(hass, freezer, 5)
    assert _read_state(_manager(entry)) == _reading(1, 3)
    await _advance(hass, freezer, 5)
    await _set(hass, TOTAL, "100.05", "kWh")
    await _unplug(hass, freezer)
    return (await _stored(hass))[0], entry


def _manager(entry: MockConfigEntry) -> SessionManager:
    return entry.runtime_data.manager


@pytest.mark.parametrize("source", ["entity", "register"])
async def test_a_known_card_identifies_the_vehicle_whatever_its_source(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> None:
    """A card read from the register is matched like one an entity reports."""
    await _setup_with_card(hass, monkeypatch, source, GLB_REPORTED, vehicles=(_glb(), _eqb()))
    await _start_charging(hass, freezer)
    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"

    await _advance(hass, freezer, 8)
    await _advance(hass, freezer, 5)

    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
    await _unplug(hass, freezer)
    session = (await _stored(hass))[0]
    assert session.vehicle_id == "v001"
    assert session.vehicle_name == "GLB"
    assert session.identification_source == "rfid"
    assert session.card_uid == GLB_CARD
    assert session.card_label == "Card GLB"
    assert session.id.endswith("_v001")


@pytest.mark.parametrize("source", ["entity", "register"])
async def test_an_unknown_card_is_treated_alike_whatever_its_source(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> None:
    """A card no vehicle holds: the session stays unassigned, in full, with a repair issue."""
    entry, _ = await _setup_with_card(
        hass, monkeypatch, source, UNKNOWN_REPORTED, vehicles=(_glb(), _eqb())
    )
    await _set(hass, GLB_TRACKER, "home")
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 8)
    await _advance(hass, freezer, 5)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")

    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.vehicle_id is None
    assert session.identification_source == "unresolved"
    assert session.status == "followup_open"
    assert session.card_uid == UNKNOWN_REPORTED
    assert session.energy_measured_kwh == pytest.approx(1.0)
    assert _issue(hass, problems.unknown_card_issue_id(_wallbox_subentry_id(entry))) is not None


@pytest.mark.parametrize("source", ["entity", "register"])
async def test_a_card_and_a_different_vehicle_report_conflict_whatever_the_source(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> None:
    """The card wins and the session is flagged, for a card from either source."""
    await _setup_with_card(hass, monkeypatch, source, GLB_REPORTED, vehicles=(_glb(), _eqb()))
    await _set(hass, GLB_TRACKER, "not_home")
    await _set(hass, EQB_TRACKER, "home")

    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 8)
    await _advance(hass, freezer, 5)
    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.vehicle_id == "v001"
    assert session.identification_conflict is True
    assert session.status == "flagged"


async def test_the_first_sequence_reads_after_ten_seconds_at_most_ten_times(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """From ten seconds after the session began, every five seconds, at most ten reads."""
    device = install(monkeypatch, FakeDevice([_unreachable()]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    assert len(device.clients) == 0

    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 9)
    assert len(device.clients) == 0
    await _advance(hass, freezer, 1)
    assert len(device.clients) == 1
    for expected in range(2, 11):
        await _advance(hass, freezer, 4)
        assert len(device.clients) == expected - 1
        await _advance(hass, freezer, 1)
        assert len(device.clients) == expected

    await _advance(hass, freezer, 3600)

    assert len(device.clients) == 10
    assert hass.states.get("sensor.carport_wallbox_state").state == "paused"
    assert not _direct_read_issue(hass, entry, "direct_read_unreachable")
    assert not _direct_read_issue(hass, entry, "direct_read_invalid_value")


async def test_the_second_sequence_starts_with_the_first_phase_and_replaces_the_first(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first phase begins another sequence at once, and the repair issue follows its end."""
    device = install(monkeypatch, FakeDevice([_unreachable()]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 10)
    await _advance(hass, freezer, 2)
    assert len(device.clients) == 1

    await _set(hass, POWER, "7.0", "kW")
    assert len(device.clients) == 2
    await _advance(hass, freezer, 3)
    assert len(device.clients) == 2
    await _advance(hass, freezer, 2)
    assert len(device.clients) == 3
    for expected in range(4, 12):
        assert not _direct_read_issue(hass, entry, "direct_read_unreachable")
        await _advance(hass, freezer, 5)
        assert len(device.clients) == expected

    assert _direct_read_issue(hass, entry, "direct_read_unreachable")
    assert not _direct_read_issue(hass, entry, "direct_read_invalid_value")
    await _advance(hass, freezer, 3600)
    assert len(device.clients) == 11
    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"


async def test_the_second_sequence_runs_after_a_first_that_ended_without_a_value(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing is read while the session waits, then the first phase reads once more."""
    device = install(monkeypatch, FakeDevice([_unreachable()] * 10 + [_card(GLB_REPORTED)]))
    entry, manager = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 10)
    await _advance_by(hass, freezer, 5, 9)
    assert len(device.clients) == 10
    assert _read_state(manager) == _reading(1, 10, "waiting")
    await _advance(hass, freezer, 3600)
    assert len(device.clients) == 10

    await _set(hass, POWER, "7.0", "kW")

    assert len(device.clients) == 11
    assert _read_state(manager) == _reading(2, 1, "read")
    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
    await _advance(hass, freezer, 3600)
    assert len(device.clients) == 11
    assert not _direct_read_issue(hass, entry, "direct_read_unreachable")


async def test_a_value_of_zero_is_a_failed_read_and_is_repeated(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Zero is no card: ten reads, a repair issue of its own, and an unassigned session."""
    device = install(monkeypatch, FakeDevice([_card(NOTHING_READ)]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    subentry_id = _wallbox_subentry_id(entry)

    await _start_charging(hass, freezer)
    assert len(device.clients) == 1
    await _advance_by(hass, freezer, 5, 8)
    assert len(device.clients) == 9
    assert not _direct_read_issue(hass, entry, "direct_read_invalid_value")
    await _advance(hass, freezer, 5)
    await _advance(hass, freezer, 600)

    assert len(device.clients) == 10
    assert _direct_read_issue(hass, entry, "direct_read_invalid_value")
    assert not _direct_read_issue(hass, entry, "direct_read_unreachable")
    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"
    assert _issue(hass, problems.unknown_card_issue_id(subentry_id)) is None
    await _unplug(hass, freezer)
    session = (await _stored(hass))[0]
    assert session.identification_source == "unresolved"
    assert session.card_uid is None


async def test_the_kind_of_the_repair_issue_follows_the_last_read(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Zero for nine reads and then no answer makes the device unreachable."""
    install(monkeypatch, FakeDevice([_card(NOTHING_READ)] * 9 + [_unreachable()]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))

    await _start_charging(hass, freezer)
    await _advance_by(hass, freezer, 5, 9)

    assert _direct_read_issue(hass, entry, "direct_read_unreachable")
    assert not _direct_read_issue(hass, entry, "direct_read_invalid_value")


async def test_the_first_valid_value_ends_the_reading(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The card may appear after the start: the read that finds it is the last."""
    device = install(
        monkeypatch,
        FakeDevice([_card(NOTHING_READ), _unreachable(), _card(GLB_REPORTED)]),
    )
    entry, manager = await _setup(
        hass, wallbox=_register_wallbox(identification_window_s=30), vehicles=(_glb(),)
    )
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 10)
    await _advance(hass, freezer, 5)
    assert _read_state(manager) == _reading(1, 3)
    await _advance(hass, freezer, 5)
    assert len(device.clients) == 3
    assert _read_state(manager) == _reading(1, 3, "read")
    assert manager.live_payload()["identification_decided"] is False

    await _advance(hass, freezer, 3600)
    assert len(device.clients) == 3
    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
    await _set(hass, TOTAL, "100.05", "kWh")
    await _unplug(hass, freezer)

    session = (await _stored(hass))[0]
    assert session.vehicle_id == "v001"
    assert session.identification_source == "rfid"
    assert session.soc_start == 40
    assert "soc_start" not in session.open_fields
    assert not _direct_read_issue(hass, entry, "direct_read_unreachable")
    assert not _direct_read_issue(hass, entry, "direct_read_invalid_value")


async def test_the_decision_does_not_wait_for_the_reading(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The window decides even with no identification: the vehicle report identifies."""
    install(monkeypatch, FakeDevice([_unreachable()]))
    _, manager = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(), _eqb()))
    await _set(hass, GLB_TRACKER, "home")
    await _set(hass, EQB_TRACKER, "not_home")

    await _set(hass, PLUG, PLUGGED)
    assert manager.live_payload()["identification_decided"] is False
    await _advance(hass, freezer, 10)
    await _advance(hass, freezer, 5)

    payload = manager.live_payload()
    assert payload["identification_decided"] is True
    assert payload["identification_source"] == "vehicle_api"
    assert _read_state(manager) == _reading(1, 3)
    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
    await _set(hass, TOTAL, "100.05", "kWh")
    await _unplug(hass, freezer)
    assert (await _stored(hass))[0].identification_source == "vehicle_api"


async def test_without_an_identification_window_the_cascade_decides_at_once(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A window of zero decides when the session begins, before any read."""
    device = install(monkeypatch, FakeDevice([_unreachable()]))
    _, manager = await _setup(
        hass, wallbox=_register_wallbox(identification_window_s=0), vehicles=(_glb(),)
    )
    await _set(hass, GLB_TRACKER, "home")

    await _set(hass, PLUG, PLUGGED)

    assert manager.live_payload()["identification_decided"] is True
    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
    assert device.clients == []


async def test_a_card_read_after_the_decision_assigns_an_unassigned_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The card held up after the window: the vehicle is assigned, the start values stay open."""
    session, entry = await _run_late_card(
        hass, freezer, monkeypatch, GLB_REPORTED, vehicles=(_glb(), _eqb())
    )

    assert session.vehicle_id == "v001"
    assert session.vehicle_name == "GLB"
    assert session.capacity_kwh == 85.0
    assert session.identification_source == "rfid"
    assert session.card_uid == GLB_CARD
    assert session.card_label == "Card GLB"
    assert session.identification_conflict is False
    assert session.soc_start is None
    assert session.odometer_km is None
    assert "soc_start" in session.open_fields
    assert "odometer_km" in session.open_fields
    assert session.id.endswith("_v001")
    assert session.energy_measured_kwh == pytest.approx(0.05)
    assert not _direct_read_issue(hass, entry, "direct_read_unreachable")
    assert not _direct_read_issue(hass, entry, "direct_read_invalid_value")


async def test_a_late_card_of_the_vehicle_the_report_chose_only_changes_the_source(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The vehicle report and the card agree: the start values stay, and there is no conflict."""
    session, _ = await _run_late_card(
        hass,
        freezer,
        monkeypatch,
        GLB_REPORTED,
        vehicles=(_glb(), _eqb()),
        trackers={GLB_TRACKER: "home", EQB_TRACKER: "not_home"},
    )

    assert session.vehicle_id == "v001"
    assert session.identification_source == "rfid"
    assert session.card_uid == GLB_CARD
    assert session.identification_conflict is False
    assert session.status != "flagged"
    assert session.soc_start == 40
    assert session.odometer_km == 7699


async def test_a_late_card_of_another_vehicle_wins_and_flags_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The card wins over the vehicle report: the vehicle changes, the start values are open."""
    session, _ = await _run_late_card(
        hass,
        freezer,
        monkeypatch,
        EQB_REPORTED,
        vehicles=(_glb(), _eqb()),
        trackers={GLB_TRACKER: "home", EQB_TRACKER: "not_home"},
    )

    assert session.vehicle_id == "v002"
    assert session.vehicle_name == "EQB"
    assert session.capacity_kwh == 70.5
    assert session.identification_source == "rfid"
    assert session.card_uid == EQB_CARD
    assert session.identification_conflict is True
    assert session.status == "flagged"
    assert session.soc_start is None
    assert session.odometer_km is None
    assert {"soc_start", "odometer_km"} <= set(session.open_fields)
    assert session.location_conflict is True
    assert session.energy_measured_kwh == pytest.approx(0.05)


async def test_an_unknown_card_read_late_leaves_an_unassigned_session_unassigned(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The card is kept and reported, and nothing is assigned."""
    session, entry = await _run_late_card(
        hass, freezer, monkeypatch, UNKNOWN_REPORTED, vehicles=(_glb(), _eqb())
    )

    assert session.vehicle_id is None
    assert session.identification_source == "unresolved"
    assert session.card_uid == UNKNOWN_REPORTED
    assert session.identification_conflict is False
    assert session.status == "followup_open"
    assert _issue(hass, problems.unknown_card_issue_id(_wallbox_subentry_id(entry))) is not None


async def test_a_late_unknown_card_flags_a_session_the_vehicle_report_assigned(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The vehicle stays, and the disagreement is marked."""
    session, entry = await _run_late_card(
        hass,
        freezer,
        monkeypatch,
        UNKNOWN_REPORTED,
        vehicles=(_glb(), _eqb()),
        trackers={GLB_TRACKER: "home", EQB_TRACKER: "not_home"},
    )

    assert session.vehicle_id == "v001"
    assert session.identification_source == "vehicle_api"
    assert session.card_uid == UNKNOWN_REPORTED
    assert session.identification_conflict is True
    assert session.status == "flagged"
    assert session.soc_start == 40
    assert _issue(hass, problems.unknown_card_issue_id(_wallbox_subentry_id(entry))) is not None


async def test_a_late_ending_that_fits_two_cards_assigns_nothing(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two cards end alike: no vehicle is guessed, and no repair issue is raised."""
    first = _glb(cards=(Card(uid="AAAA11223344", label="a"),))
    second = _eqb(cards=(Card(uid="BBBB11223344", label="b"),))

    session, entry = await _run_late_card(
        hass, freezer, monkeypatch, GLB_REPORTED, vehicles=(first, second)
    )

    assert session.vehicle_id is None
    assert session.identification_source == "unresolved"
    assert session.identification_conflict is False
    assert _issue(hass, problems.unknown_card_issue_id(_wallbox_subentry_id(entry))) is None


async def test_a_late_card_changes_neither_energy_nor_cost_nor_phases(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the assignment moves; what was measured stays as it was."""
    install(monkeypatch, FakeDevice([_card(NOTHING_READ)] * 3 + [_card(GLB_REPORTED)]))
    _, manager = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 5)
    await _set(hass, TOTAL, "100.1", "kWh")
    await _advance(hass, freezer, 5)
    await _set(hass, TOTAL, "100.2", "kWh")
    await _advance(hass, freezer, 3)
    assert hass.states.get("sensor.carport_active_vehicle").state == "unresolved"
    before = manager.live_payload()

    await _advance(hass, freezer, 2)

    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
    after = manager.live_payload()
    for key in ("energy_kwh", "energy_grid_kwh", "energy_solar_kwh", "cost", "phase_count"):
        assert after[key] == before[key], key
    assert after["energy_kwh"] == pytest.approx(0.2)
    await _unplug(hass, freezer)
    session = (await _stored(hass))[0]
    assert session.vehicle_id == "v001"
    assert session.energy_measured_kwh == pytest.approx(0.2)
    assert session.energy_grid_kwh == pytest.approx(before["energy_grid_kwh"])
    assert session.energy_solar_kwh == pytest.approx(before["energy_solar_kwh"])
    assert session.cost == pytest.approx(before["cost"])
    assert session.phase_count == 1


async def test_a_candidate_that_is_dropped_stops_the_reading(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A brief peak of power that does not become a session leaves no read behind."""
    device = install(monkeypatch, FakeDevice([_unreachable()]))
    _, manager = await _setup(hass, wallbox=_register_wallbox(), plug="undefined")

    await _set(hass, POWER, "7.0", "kW")
    assert _read_state(manager) == _reading(1, 1)
    await _advance(hass, freezer, 1)
    await _set(hass, POWER, "0", "kW")
    assert hass.states.get("sensor.carport_wallbox_state").state == "idle"
    assert _read_state(manager) is None

    await _advance(hass, freezer, 60)

    assert device.clients == []


async def test_a_flicker_of_the_plug_stops_the_reading(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A connector report that does not last leaves no read behind either."""
    device = install(monkeypatch, FakeDevice([_unreachable()]))
    await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))

    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 1)
    await _set(hass, PLUG, UNPLUGGED)
    await _advance(hass, freezer, 60)

    assert device.clients == []


async def test_a_session_that_ends_first_stops_the_reading_and_raises_no_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unplugging before the second sequence is over leaves neither a read nor an issue."""
    device = install(monkeypatch, FakeDevice([_unreachable()]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))

    await _start_charging(hass, freezer)
    await _advance_by(hass, freezer, 5, 2)
    assert len(device.clients) == 3
    await _unplug(hass, freezer)
    await _advance(hass, freezer, 600)

    assert len(device.clients) == 3
    assert not _direct_read_issue(hass, entry, "direct_read_unreachable")
    assert not _direct_read_issue(hass, entry, "direct_read_invalid_value")
    assert len(await _stored(hass)) == 1


async def test_the_reading_is_taken_up_again_after_a_restart(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A restored session whose card was not read reads again, counted from its start."""
    device = install(monkeypatch, FakeDevice([_card(GLB_REPORTED)]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 3)
    assert len(device.clients) == 0
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _advance(hass, freezer, 6)
    assert len(device.clients) == 0
    await _advance(hass, freezer, 1)
    assert len(device.clients) == 1
    await _advance(hass, freezer, 5)

    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"


async def test_a_restored_session_that_already_charged_reads_at_once(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first phase has begun, so the restored session goes straight to a sequence."""
    device = install(monkeypatch, FakeDevice([_unreachable()]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    await _start_charging(hass, freezer)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    reads_before = len(device.clients)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(device.clients) == reads_before + 1


async def test_a_restored_session_that_holds_its_card_does_not_read_again(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Once the card is held for the session, a restart needs no further read."""
    device = install(monkeypatch, FakeDevice([_card(GLB_REPORTED)]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 13)
    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"
    reads_before = len(device.clients)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _advance(hass, freezer, 3600)

    assert len(device.clients) == reads_before
    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"


async def test_the_progress_of_the_reading_is_reported_on_the_live_payload(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sequence, attempt and maximum while reading, then waiting, unreadable or read."""
    install(monkeypatch, FakeDevice([_unreachable()]))
    _, manager = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    assert _read_state(manager) is None

    await _set(hass, PLUG, PLUGGED)
    assert _read_state(manager) == _reading(1, 1)
    await _advance(hass, freezer, 10)
    assert _read_state(manager) == _reading(1, 2)
    await _advance_by(hass, freezer, 5, 9)
    assert _read_state(manager) == _reading(1, 10, "waiting")

    await _set(hass, POWER, "7.0", "kW")
    assert _read_state(manager) == _reading(2, 2)
    await _advance_by(hass, freezer, 5, 9)
    assert _read_state(manager) == _reading(2, 10, "unreadable")

    await _unplug(hass, freezer)
    assert _read_state(manager) is None


async def test_the_live_payload_has_no_reading_state_for_an_entity(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The card is not told whether the identification comes from an entity or a register."""
    _, manager = await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, GLB_REPORTED)

    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 20)

    assert manager.live_payload()["identification_decided"] is True
    assert _read_state(manager) is None


async def test_no_read_takes_place_while_no_vehicle_is_plugged_in(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No read without a session, however long that lasts; with one, the first is delayed."""
    device = install(monkeypatch, FakeDevice([_card(GLB_REPORTED)]))
    await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))

    await _advance(hass, freezer, 3600)
    assert device.reads == []

    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 9)
    assert device.reads == []
    await _advance(hass, freezer, 1)
    assert device.reads == [(1500, 2, 255)]


async def test_the_connection_settings_of_the_wallbox_are_used(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Address, port and unit id of the wallbox decide where and as whom the register is read."""
    device = install(monkeypatch, FakeDevice([_card(GLB_REPORTED)]))
    await _setup(
        hass,
        wallbox=_register_wallbox(host="192.0.2.77", port=1502, unit_id=7),
        vehicles=(_glb(),),
    )

    await _start_charging(hass, freezer)

    assert device.clients[0].host == "192.0.2.77"
    assert device.clients[0].kwargs["port"] == 1502
    assert device.reads == [(1500, 2, 7)]


async def test_nothing_is_read_or_imported_while_the_direct_read_is_off(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without an address, or without the register as the source, there is no client at all."""
    device = install(monkeypatch, FakeDevice([_card(GLB_REPORTED)]))
    entry, _ = await _setup(hass, vehicles=(_glb(),))
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)
    await _unplug(hass, freezer)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    for overrides in (
        {"host": None},
        {"identification_from_register": False},
    ):
        wallbox = _register_wallbox(**overrides)
        subentry = next(iter(entry.subentries.values()))
        hass.config_entries.async_update_subentry(entry, subentry, data=wallbox)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        await _start_charging(hass, freezer)
        await _advance(hass, freezer, 20)
        await _unplug(hass, freezer)
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert device.imports == 0
    assert device.clients == []


async def test_the_library_is_imported_when_the_wallbox_is_set_up_for_it(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Switching the direct read on is what brings the library in, and no session is needed."""
    device = install(monkeypatch, FakeDevice([_card(GLB_REPORTED)]))

    await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))

    assert device.imports == 1
    assert device.clients == []


async def test_a_later_read_that_succeeds_clears_the_repair_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The issue stands until the register can be read again."""
    install(monkeypatch, FakeDevice([_unreachable()] * 10 + [_card(GLB_REPORTED)]))
    entry, _ = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))

    await _start_charging(hass, freezer)
    await _advance_by(hass, freezer, 5, 9)
    assert _direct_read_issue(hass, entry, "direct_read_unreachable") is not None
    await _unplug(hass, freezer)
    assert _direct_read_issue(hass, entry, "direct_read_unreachable") is not None

    await _start_charging(hass, freezer)

    assert _direct_read_issue(hass, entry, "direct_read_unreachable") is None
    await _advance(hass, freezer, 13)
    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"


async def test_a_stale_repair_issue_is_cleared_when_the_integration_starts(
    hass: HomeAssistant,
) -> None:
    """After a change of the settings no old issue about the direct read remains."""
    entry, _ = await _setup(hass, vehicles=(_glb(),))
    subentry_id = _wallbox_subentry_id(entry)
    problems.check_direct_read(
        hass, failure="unreachable", wallbox_id=subentry_id, wallbox_title="Carport"
    )
    issue_id = problems.direct_read_issue_id("direct_read_unreachable", subentry_id)
    assert _issue(hass, issue_id) is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert _issue(hass, issue_id) is None


async def test_a_failing_reading_logs_one_warning_and_no_flood(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Ten failed reads make one warning, and a further failing session none."""
    install(monkeypatch, FakeDevice([_unreachable()]))
    await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    caplog.set_level(logging.INFO, logger="custom_components.ev_charging")

    await _start_charging(hass, freezer)
    await _advance_by(hass, freezer, 5, 9)
    await _advance(hass, freezer, 60)
    await _unplug(hass, freezer)
    await _start_charging(hass, freezer)
    await _advance_by(hass, freezer, 5, 9)
    await _advance(hass, freezer, 60)

    warnings = [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.WARNING and record.pathname.endswith("session_manager.py")
    ]
    assert len(warnings) == 1
    assert "could not be read from the wallbox" in warnings[0]


async def test_the_card_read_from_the_register_is_never_logged(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Neither the value read nor the stored card shows up in the log, at any level."""
    install(monkeypatch, FakeDevice([_card(GLB_REPORTED)]))
    await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    caplog.set_level(logging.DEBUG)

    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 13)
    await _unplug(hass, freezer)

    assert (await _stored(hass))[0].vehicle_id == "v001"
    text = " ".join(
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("custom_components")
    ).lower()
    assert GLB_REPORTED.lower() not in text
    assert GLB_CARD.lower() not in text


async def test_the_live_payload_carries_no_card_when_the_register_is_read(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reading state names sequence and attempt, never the value."""
    install(monkeypatch, FakeDevice([_card(GLB_REPORTED)]))
    _, manager = await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    await _start_charging(hass, freezer)

    rendered = str(manager.live_payload())

    for value in (GLB_REPORTED, GLB_CARD, "Card GLB"):
        assert value not in rendered


async def test_the_debug_log_traces_the_session_and_the_reading_without_the_identification(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The log shows the plug, the state changes, every read and what came of the card."""
    install(
        monkeypatch,
        FakeDevice([_unreachable(), _card(NOTHING_READ), _card(GLB_REPORTED)]),
    )
    await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    caplog.set_level(logging.DEBUG, logger="custom_components.ev_charging")

    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 10)
    await _advance(hass, freezer, 5)
    await _advance(hass, freezer, 5)
    await _set(hass, POWER, "7.0", "kW")

    text = "\n".join(
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("custom_components")
    )
    for line in (
        "Plug state 'plugged_and_locked' reads as connected",
        "A candidate begins, started by the plug",
        "Session state candidate -> paused",
        "the first sequence of reads begins in 10 s",
        "Read of 192.0.2.10:502, unit 255, register 1500: no connection",
        "Identification: sequence 1, read 1 of 10: no valid answer from the device",
        "Identification: sequence 1, read 2 of 10: the register holds 0",
        "Identification decided: source unresolved, vehicle None, card read False, conflict False",
        "Identification: sequence 1, read 3 of 10: identification read, ends in ..44",
        "Identification read after the decision: source rfid, vehicle v001, conflict False",
        "Phase 1 begins",
        "Session state paused -> charging",
    ):
        assert line in text, line
    assert "no second sequence, it was already read" in text
    assert GLB_REPORTED not in text
    assert GLB_CARD not in text
    assert all(
        record.levelno == logging.DEBUG
        for record in caplog.records
        if record.name.startswith("custom_components") and "Read of" in record.getMessage()
    )


async def test_the_debug_log_says_why_a_session_is_not_stored(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A session that held nothing is dropped, and the log says so."""
    await _setup(hass)
    caplog.set_level(logging.DEBUG, logger="custom_components.ev_charging")
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 60)

    await _unplug(hass, freezer)

    text = "\n".join(record.getMessage() for record in caplog.records)
    assert "The session ends: 0 phases, it holds nothing and is not stored" in text


# ----------------------------------------------------- external sessions (7.4, 7.5, 4.7)

CHARGING_DC = "14"  # Mercedes: DC charging active
CHARGING_AC = "13"  # Mercedes: AC charging active
CONNECTED_IDLE = "8"  # Mercedes: connected, not charging
DISCONNECTED = "3"  # Mercedes: not connected
ERROR_CODE = "4"  # Mercedes: charging error
NEUTRAL_MISSING = "error"  # Mercedes: attribute absent, neutral for both roles
UNMAPPED = "99"  # not present in the mbapi2020 mapping at all


def _glb_ext(**overrides: Any) -> dict[str, Any]:
    """A GLB whose charge_type role is fed by the same entity as charge_state (4.7)."""
    return _glb(charge_type=_role(GLB_CHARGE), **overrides)


def _external_block(manager: SessionManager, vehicle_id: str) -> dict[str, Any] | None:
    return next(
        (
            block
            for block in manager.live_blocks()
            if block["kind"] == "external"
            and block["vehicle"] is not None
            and block["vehicle"]["id"] == vehicle_id
        ),
        None,
    )


async def test_external_session_begins_only_from_charging(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """connected_idle alone, without a prior charging report, starts no session (I17)."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))

    await _set(hass, GLB_CHARGE, CONNECTED_IDLE)
    await _advance(hass, freezer, 1)
    assert _external_block(manager, "v001") is None

    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 1)
    block = _external_block(manager, "v001")
    assert block is not None
    assert block["state"] == SESSION_STATE_CHARGING


async def test_external_session_location_is_home_no_wallbox_in_the_home_zone(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A vehicle charging while its tracker reports the home zone is home_no_wallbox (7.4)."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))

    await _set(hass, GLB_TRACKER, "home")
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    block = _external_block(manager, "v001")
    assert block is not None
    assert block["location"] == LOCATION_HOME_NO_WALLBOX


@pytest.mark.parametrize("tracker_state", ["not_home", "unknown", "unavailable"])
async def test_external_session_location_is_external_outside_the_home_zone(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, tracker_state: str
) -> None:
    """Anything but the home zone, including an unusable tracker, is external (7.4)."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))

    await _set(hass, GLB_TRACKER, tracker_state)
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    block = _external_block(manager, "v001")
    assert block is not None
    assert block["location"] == LOCATION_EXTERNAL


async def test_the_wallbox_already_charging_this_vehicle_suppresses_its_external_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A vehicle the wallbox already claims never gets a second, external block (7.4)."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, GLB_TRACKER, "home")
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 15)
    assert manager.live_payload()["vehicle"]["id"] == "v001"

    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is None
    assert len(manager.live_blocks()) == 1


async def test_an_unmapped_value_during_an_external_session_stays_open_and_flags_an_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A raw value outside the mapping never ends an external session (I15)."""
    entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    vehicle_subentry_id = next(
        s.subentry_id for s in entry.subentries.values() if s.subentry_type == SUBENTRY_TYPE_VEHICLE
    )
    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 1)

    await _set(hass, GLB_CHARGE, UNMAPPED)
    await _advance(hass, freezer, 1)

    block = _external_block(manager, "v001")
    assert block is not None
    assert block["state"] != SESSION_STATE_ERROR
    issue = _issue(hass, f"unknown_mapping_value_{vehicle_subentry_id}_charge_state")
    assert issue is not None

    await _set(hass, GLB_CHARGE, ERROR_CODE)
    await _advance(hass, freezer, 1)
    block = _external_block(manager, "v001")
    assert block is not None
    assert block["state"] == SESSION_STATE_ERROR
    assert block["charge_error"] is True


async def test_charge_type_of_an_external_session_locks_on_the_first_report_and_warns_after(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The first ac/dc report wins for good; a later, differing one only warns (E32, I21)."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    caplog.set_level(logging.WARNING, logger="custom_components.ev_charging")

    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 1)
    assert _external_block(manager, "v001")["charge_type"] == "dc"

    await _set(hass, GLB_CHARGE, "9")  # neutral charge_type, charging
    await _advance(hass, freezer, 1)
    assert _external_block(manager, "v001")["charge_type"] == "dc"

    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)
    block = _external_block(manager, "v001")
    assert block["charge_type"] == "dc"
    assert block["state"] == SESSION_STATE_CHARGING
    assert block["flagged"] is False
    assert any("differs from the established" in record.getMessage() for record in caplog.records)

    caplog.clear()
    await _set(hass, GLB_CHARGE, NEUTRAL_MISSING)
    await _advance(hass, freezer, 1)
    block = _external_block(manager, "v001")
    assert block["state"] == SESSION_STATE_CHARGING
    assert not any(
        record.levelno >= logging.WARNING and record.name.startswith("custom_components")
        for record in caplog.records
    )


async def test_an_external_session_ends_only_on_disconnected_and_is_stored(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The finished external session is written with the fields 7.4/8.5 call for."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, GLB_TRACKER, "not_home")
    await _set(hass, GLB_SOC, "40", "%")
    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 1)
    await _set(hass, GLB_SOC, "55", "%")
    await _advance(hass, freezer, 60)

    await _set(hass, GLB_CHARGE, DISCONNECTED)
    await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is None
    (stored,) = await _stored(hass)
    assert stored.location == LOCATION_EXTERNAL
    assert stored.vehicle_id == "v001"
    assert stored.wallbox_id is None
    assert stored.identification_source == "vehicle_api"
    assert stored.charge_type == "dc"
    assert stored.soc_start == 40
    assert stored.soc_end == 55
    assert stored.energy_raw_kwh == pytest.approx(85.0 * 0.15)
    assert stored.energy_kwh == pytest.approx(85.0 * 0.15)
    assert stored.cost is None
    assert "cost" in stored.open_fields
    assert stored.phase_count == 1


async def test_an_external_session_never_stays_disconnected_forever_empty(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A charging report always opens a phase, so the empty-session discard never applies."""
    _entry, _manager = await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    await _set(hass, GLB_CHARGE, DISCONNECTED)
    await _advance(hass, freezer, 1)

    assert len(await _stored(hass)) == 1


async def test_an_external_session_reports_the_vehicles_own_session_energy_when_present(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """energy_session from the vehicle is authoritative and never marked as an estimate."""
    _entry, manager = await _setup(
        hass, vehicles=(_glb_ext(energy_session=_role("sensor.glb_energy", "kWh")),)
    )
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)
    await _set(hass, "sensor.glb_energy", "4.2", "kWh")
    await _advance(hass, freezer, 1)

    block = _external_block(manager, "v001")
    assert block["energy_kwh"] == pytest.approx(4.2)
    assert block["energy_is_estimate"] is False


async def test_an_external_session_estimates_energy_from_soc_without_a_reported_value(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Without energy_session, energy is estimated from the state of charge and marked so."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, GLB_SOC, "40", "%")
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)
    await _set(hass, GLB_SOC, "50", "%")
    await _advance(hass, freezer, 1)

    block = _external_block(manager, "v001")
    assert block["energy_kwh"] == pytest.approx(8.5)
    assert block["energy_is_estimate"] is True


async def test_two_vehicles_can_charge_externally_at_once_in_start_order(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Several running external sessions coexist, ordered by when they began (11.1)."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(), _eqb(charge_type=_role(EQB_CHARGE))))

    await _set(hass, EQB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 5)
    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 1)

    blocks = manager.live_blocks()
    assert blocks[0]["kind"] == "wallbox"
    assert [block["vehicle"]["id"] for block in blocks[1:]] == ["v002", "v001"]


async def test_an_external_sessions_source_going_unavailable_times_out_after_the_session_timeout(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A charge_state that stays unusable for the full timeout closes the session, flagged (7.5)."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    hass.states.async_set(GLB_CHARGE, "unavailable")
    await hass.async_block_till_done()
    await _advance(hass, freezer, 12 * 3600 + 5)

    assert _external_block(manager, "v001") is None
    (stored,) = await _stored(hass)
    assert stored.status == SESSION_STATUS_FLAGGED


async def test_an_external_session_looks_up_and_shows_its_address(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, aioclient_mock: AiohttpClientMocker
) -> None:
    """A newly started external session resolves its address from the tracker's coordinates."""
    aioclient_mock.get(
        "https://nominatim.openstreetmap.org/reverse", json={"display_name": "Marienplatz, München"}
    )
    _entry, manager = await _setup(
        hass,
        vehicles=(_glb_ext(),),
        hub=_hub(geocoding_enabled=True, geocoding_contact="test@example.invalid"),
    )
    hass.states.async_set(GLB_TRACKER, "not_home", {"latitude": 48.1, "longitude": 11.6})
    await hass.async_block_till_done()
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await hass.async_block_till_done()
    await _advance(hass, freezer, 1)

    block = _external_block(manager, "v001")
    assert block is not None
    assert block["address"] == "Marienplatz, München"


async def test_vehicle_session_active_binary_sensor_follows_the_external_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The vehicle-level snapshot reflects its own session, independent of the wallbox."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    assert manager.vehicle_snapshots["v001"].session_active is False

    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)
    assert manager.vehicle_snapshots["v001"].session_active is True
    assert manager.vehicle_snapshots["v001"].session_state == SESSION_STATE_CHARGING

    await _set(hass, GLB_CHARGE, DISCONNECTED)
    await _advance(hass, freezer, 1)
    assert manager.vehicle_snapshots["v001"].session_active is False


async def test_a_restarted_external_session_keeps_running_across_reload(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """An external session in progress survives an unload and setup of the entry."""
    entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)
    assert _external_block(manager, "v001") is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    restarted_manager = entry.runtime_data.manager
    assert restarted_manager is not None
    block = _external_block(restarted_manager, "v001")
    assert block is not None
    assert block["state"] == SESSION_STATE_CHARGING


# ------------------------------- the car at the wallbox and the vehicle's plug state

GLB_PLUG = "sensor.glb_plug"
GLB_POWER = "sensor.glb_power"
PLUG_VEHICLE = "vehicle plugged"
PLUG_VEHICLE_NOT = "vehicle not plugged"


def _glb_unidentified(**overrides: Any) -> dict[str, Any]:
    """A GLB the wallbox cannot identify: no card and no identification by the vehicle report."""
    return _glb_ext(identify_by_vehicle_api=False, cards=(), **overrides)


@pytest.mark.parametrize(
    ("session_age_s", "edge_age_s", "charging", "expected"),
    [
        (10, None, False, True),
        (120, None, False, True),
        (121, None, False, False),
        (3600, None, True, True),
        (3600, 60, False, True),
        (3600, 121, False, False),
        (3600, None, False, False),
    ],
)
def test_the_window_decides_whether_a_vehicle_is_the_car_at_the_wallbox(
    session_age_s: float, edge_age_s: float | None, charging: bool, expected: bool
) -> None:
    """Session start, charging now, or a recent rise or fall of the power count."""
    assert (
        is_wallbox_vehicle(
            session_age_s=session_age_s,
            charge_edge_age_s=edge_age_s,
            wallbox_charging=charging,
            wallbox_power_kw=None,
            vehicle_power_kw=None,
        )
        is expected
    )


@pytest.mark.parametrize(
    ("wallbox_kw", "vehicle_kw", "expected"),
    [
        (7.0, 6.5, True),
        (7.0, 5.25, True),
        (7.0, 5.0, False),
        (7.0, 9.0, False),
        (11.0, 8.5, True),
        (11.0, 8.0, False),
        (2.0, 0.5, True),
        (2.0, 0.4, False),
        (7.0, None, True),
        (7.0, 0.0, True),
        (None, 3.0, True),
    ],
)
def test_powers_that_differ_beyond_the_tolerance_mean_another_car(
    wallbox_kw: float | None, vehicle_kw: float | None, expected: bool
) -> None:
    """The tolerance is the larger of 1.5 kW and a quarter of the wallbox power."""
    assert (
        is_wallbox_vehicle(
            session_age_s=10,
            charge_edge_age_s=None,
            wallbox_charging=True,
            wallbox_power_kw=wallbox_kw,
            vehicle_power_kw=vehicle_kw,
        )
        is expected
    )


async def test_a_vehicle_reporting_charging_with_the_wallbox_gets_no_external_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The car the wallbox cannot identify is still the car at the wallbox."""
    _entry, manager = await _setup(hass, vehicles=(_glb_unidentified(),))
    await _set(hass, GLB_TRACKER, "home")
    await _start_charging(hass, freezer)

    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)
    assert _external_block(manager, "v001") is None

    await _advance(hass, freezer, 30)
    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is None
    assert len(manager.live_blocks()) == 1
    assert manager.live_payload()["identification_source"] == "unresolved"


async def test_the_verdict_holds_while_the_wallbox_pauses_beyond_the_window(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A later report in a long pause still begins nothing, also after a reload."""
    entry, manager = await _setup(hass, vehicles=(_glb_unidentified(),))
    await _set(hass, GLB_TRACKER, "home")
    await _start_charging(hass, freezer)
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)
    await _set(hass, POWER, "0", "kW")
    await _advance(hass, freezer, 400)

    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 1)
    assert _external_block(manager, "v001") is None

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    manager = entry.runtime_data.manager
    assert manager is not None
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is None


async def test_a_vehicle_reporting_charging_long_after_the_wallbox_session_began_is_another_car(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """With no charging at the wallbox in the window, the report is not the car at the wallbox."""
    _entry, manager = await _setup(hass, vehicles=(_glb_unidentified(),))
    await _set(hass, GLB_TRACKER, "home")
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 300)

    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    block = _external_block(manager, "v001")
    assert block is not None
    assert block["location"] == LOCATION_HOME_NO_WALLBOX


@pytest.mark.parametrize(
    ("vehicle_kw", "external"),
    [("6.5", False), ("5.25", False), ("5.0", True), ("2.0", True), ("0", False)],
)
async def test_the_vehicle_power_tells_another_car_from_the_one_at_the_wallbox(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, vehicle_kw: str, external: bool
) -> None:
    """Both powers known and far apart mean a second car, close together mean the same."""
    _entry, manager = await _setup(
        hass, vehicles=(_glb_unidentified(charge_power=_role(GLB_POWER, "kW")),)
    )
    await _set(hass, GLB_TRACKER, "home")
    await _set(hass, GLB_POWER, vehicle_kw, "kW")
    await _start_charging(hass, freezer, power_kw=7.0)

    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    assert (_external_block(manager, "v001") is not None) is external


async def test_a_vehicle_at_home_is_another_car_once_the_wallbox_names_a_different_one(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The wallbox session already assigned to the EQB leaves the GLB its own session."""
    _entry, manager = await _setup(hass, vehicles=(_glb_unidentified(), _eqb()))
    await _set(hass, EQB_TRACKER, "home")
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)
    assert manager.live_payload()["vehicle"]["id"] == "v002"

    await _set(hass, GLB_TRACKER, "home")
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is not None


async def test_a_vehicle_outside_the_home_zone_keeps_its_external_session_beside_the_wallbox(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A vehicle that is away cannot be at the wallbox."""
    _entry, manager = await _setup(hass, vehicles=(_glb_unidentified(),))
    await _set(hass, GLB_TRACKER, "not_home")
    await _start_charging(hass, freezer)

    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 1)

    block = _external_block(manager, "v001")
    assert block is not None
    assert block["location"] == LOCATION_EXTERNAL


async def test_a_vehicle_of_an_ended_wallbox_session_begins_again_only_after_another_report(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The late report of the unplugging, still charging, does not begin a session."""
    _entry, manager = await _setup(hass, vehicles=(_glb_unidentified(),))
    await _set(hass, GLB_TRACKER, "home")
    await _start_charging(hass, freezer)
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 60)
    await _unplug(hass, freezer)
    assert len(await _stored(hass)) == 1

    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 1)
    assert _external_block(manager, "v001") is None

    await _set(hass, GLB_CHARGE, CONNECTED_IDLE)
    await _advance(hass, freezer, 1)
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    block = _external_block(manager, "v001")
    assert block is not None
    assert block["location"] == LOCATION_HOME_NO_WALLBOX


async def test_a_vehicle_that_was_not_charging_at_the_end_of_the_wallbox_session_is_not_held_back(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Only a vehicle that still reports charging waits for another report."""
    _entry, manager = await _setup(hass, vehicles=(_glb_unidentified(),))
    await _set(hass, GLB_TRACKER, "home")
    await _start_charging(hass, freezer)
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 60)
    await _set(hass, GLB_CHARGE, CONNECTED_IDLE)
    await _advance(hass, freezer, 1)
    await _unplug(hass, freezer)

    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is not None


async def _start_external_with_plug(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> tuple[MockConfigEntry, SessionManager]:
    hass.states.async_set(GLB_PLUG, PLUG_VEHICLE)
    entry, manager = await _setup(hass, vehicles=(_glb_unidentified(plug_state=_role(GLB_PLUG)),))
    await _set(hass, GLB_TRACKER, "not_home")
    await _set(hass, GLB_CHARGE, CHARGING_AC)
    await _advance(hass, freezer, 1)
    assert _external_block(manager, "v001") is not None
    return entry, manager


async def test_the_vehicle_plug_state_not_connected_ends_its_external_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The session ends and is stored, without the charge state reporting anything."""
    _entry, manager = await _start_external_with_plug(hass, freezer)
    await _advance(hass, freezer, 60)

    await _set(hass, GLB_PLUG, PLUG_VEHICLE_NOT)
    await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is None
    (stored,) = await _stored(hass)
    assert stored.location == LOCATION_EXTERNAL
    assert stored.vehicle_id == "v001"


@pytest.mark.parametrize("value", ["vehicle plugged", "plugged", "error"])
async def test_a_connected_or_neutral_vehicle_plug_state_never_ends_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, value: str
) -> None:
    """Connected and the neutral value change nothing, and raise no repair issue."""
    entry, manager = await _start_external_with_plug(hass, freezer)
    subentry_id = next(
        s.subentry_id for s in entry.subentries.values() if s.subentry_type == SUBENTRY_TYPE_VEHICLE
    )

    await _set(hass, GLB_PLUG, value)
    await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is not None
    assert _issue(hass, problems.unknown_mapping_value_issue_id(subentry_id, "plug_state")) is None


async def test_a_neutral_plug_value_keeps_the_last_class(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """After not connected, the neutral value does not read as connected, and nothing ends twice."""
    _entry, manager = await _start_external_with_plug(hass, freezer)
    await _set(hass, GLB_PLUG, PLUG_VEHICLE_NOT)
    await _advance(hass, freezer, 1)
    assert _external_block(manager, "v001") is None

    await _set(hass, GLB_PLUG, "error")
    await _advance(hass, freezer, 1)

    assert len(await _stored(hass)) == 1


async def test_an_unmapped_vehicle_plug_value_stays_open_and_flags_an_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A raw value outside the mapping ends nothing."""
    entry, manager = await _start_external_with_plug(hass, freezer)
    subentry_id = next(
        s.subentry_id for s in entry.subentries.values() if s.subentry_type == SUBENTRY_TYPE_VEHICLE
    )

    await _set(hass, GLB_PLUG, "something new")
    await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is not None
    assert _issue(hass, problems.unknown_mapping_value_issue_id(subentry_id, "plug_state"))


async def test_an_unusable_vehicle_plug_state_ends_nothing(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Unknown and unavailable are no plug report."""
    _entry, manager = await _start_external_with_plug(hass, freezer)

    for value in ("unavailable", "unknown"):
        await _set(hass, GLB_PLUG, value)
        await _advance(hass, freezer, 1)

    assert _external_block(manager, "v001") is not None
