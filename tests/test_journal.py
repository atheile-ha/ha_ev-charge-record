"""Tests for the journal of events and decisions and the diagnostics download."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from custom_components.ev_charging import journal, problems
from custom_components.ev_charging.const import (
    ATTR_CONFIRM,
    ATTR_SESSION_ID,
    DOMAIN,
    JOURNAL_ADMIN_ACTION,
    JOURNAL_REPAIR_ISSUE_CREATED,
    JOURNAL_REPAIR_ISSUE_DELETED,
    SERVICE_DELETE_ALL_DATA,
    SERVICE_UPDATE_SESSION,
    STORE_KEY_JOURNAL,
    STORE_KEY_RUNTIME,
)
from custom_components.ev_charging.diagnostics import async_get_config_entry_diagnostics
from custom_components.ev_charging.journal import prune, sanitize, shorten_card
from custom_components.ev_charging.store import JournalStore
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import Unauthorized
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockUser
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from tests.fake_modbus import FakeDevice, install
from tests.test_session_manager import (
    CARD,
    GLB_CARD,
    GLB_CHARGE,
    GLB_REPORTED,
    GLB_TRACKER,
    PLUG,
    PLUGGED,
    POWER,
    TIME_ZONE,
    _advance,
    _card,
    _glb,
    _register_wallbox,
    _set,
    _setup,
    _start_charging,
    _stored,
    _touch_year_file,
    _unplug,
)

VIN = "W1NSYNTHETIC000001"
ADDRESS = "Musterweg 1, 12345 Beispielstadt"
LATITUDE = 50.123456
LONGITUDE = 8.654321
CARD_LABEL = "Card GLB"

# Events of the capture itself; sources, repair issues, notifications and the
# lifecycle of the integration are left out where a test follows a session.
_NOT_CAPTURE = ("source_", "repair_issue_", "notification_", "integration_", "read")


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Give the test a private config dir: the years with data are read from disk."""
    return hass_tmp_config_dir


@pytest.fixture(autouse=True)
async def _time_zone(hass: HomeAssistant) -> None:
    """Use a fixed time zone."""
    await hass.config.async_set_time_zone(TIME_ZONE)


def _events(hass: HomeAssistant, *, capture_only: bool = False) -> list[str]:
    events = [entry["event"] for entry in journal.entries(hass)]
    if capture_only:
        events = [event for event in events if not event.startswith(_NOT_CAPTURE)]
    return events


def _entries(hass: HomeAssistant, event: str) -> list[dict[str, Any]]:
    return [entry for entry in journal.entries(hass) if entry["event"] == event]


def _stored_entry(moment: Any, event: str = "old") -> dict[str, Any]:
    return {"time": moment.isoformat(timespec="milliseconds"), "event": event}


# ---------------------------------------------------------------- pure (I25)


def test_sanitize_drops_personal_fields_and_shortens_the_card() -> None:
    """vin, card label, address and coordinates never appear; a card only by its last four."""
    details = sanitize(
        {
            "card_uid": GLB_CARD,
            "card_label": CARD_LABEL,
            "vin": VIN,
            "address": ADDRESS,
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "nested": {"vin": VIN, "card_uid": GLB_CARD, "kept": 1},
            "state": "charging",
        }
    )

    assert details == {
        "card_uid": GLB_CARD[-4:],
        "nested": {"card_uid": GLB_CARD[-4:], "kept": 1},
        "state": "charging",
    }


def test_shorten_card_keeps_an_absent_card() -> None:
    """No card stays no card."""
    assert shorten_card(None) is None
    assert shorten_card("") == ""


def test_prune_drops_entries_beyond_the_retention_time() -> None:
    """An entry older than 90 days is dropped, the order of the rest is kept."""
    now = dt_util.now()
    entries = [
        _stored_entry(now - timedelta(days=91), "too_old"),
        _stored_entry(now - timedelta(days=89), "first"),
        _stored_entry(now, "second"),
    ]

    assert [entry["event"] for entry in prune(entries, now)] == ["first", "second"]


def test_prune_keeps_the_newest_entries_up_to_the_limit() -> None:
    """Beyond the limit the oldest entries fall out."""
    now = dt_util.now()
    entries = [_stored_entry(now - timedelta(seconds=10 - i), f"e{i}") for i in range(10)]

    with patch("custom_components.ev_charging.journal.JOURNAL_MAX_ENTRIES", 3):
        kept = prune(entries, now)

    assert [entry["event"] for entry in kept] == ["e7", "e8", "e9"]


def test_prune_drops_an_entry_without_a_readable_time() -> None:
    """An entry whose time cannot be read is dropped."""
    now = dt_util.now()

    assert prune([{"event": "x"}, {"time": "garbage", "event": "y"}], now) == []


# ------------------------------------------------------- integration (I25)


async def test_an_entry_never_holds_a_full_card_a_vin_or_an_address(hass: HomeAssistant) -> None:
    """An event that touches a card, an address and a VIN keeps only the last four of the card."""
    await _setup(hass, vehicles=(_glb(),))

    journal.add(
        hass,
        "identification_decided",
        vehicle_id="v001",
        card_uid=GLB_CARD,
        card_label=CARD_LABEL,
        vin=VIN,
        address=ADDRESS,
        latitude=LATITUDE,
        longitude=LONGITUDE,
    )

    text = json.dumps(journal.entries(hass))
    for secret in (GLB_CARD, CARD_LABEL, VIN, ADDRESS, str(LATITUDE), str(LONGITUDE)):
        assert secret not in text
    assert journal.entries(hass)[-1]["data"] == {"card_uid": GLB_CARD[-4:]}


async def test_the_identification_by_card_is_journaled_with_the_card_shortened(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The cascade decision names stage and source and the card only by its last four."""
    await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, GLB_CARD)
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 15)

    (decided,) = _entries(hass, "identification_decided")
    assert decided["vehicle_id"] == "v001"
    assert decided["wallbox_id"] == "wb001"
    assert decided["data"]["stage"] == 1
    assert decided["data"]["source"] == "rfid"
    assert decided["data"]["card_uid"] == GLB_CARD[-4:]
    assert GLB_CARD not in json.dumps(journal.entries(hass))


async def test_diagnostics_redact_personal_fields_and_hold_the_journal(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Hub, subentries, runtime state and journal, without VIN, card, label or address."""
    entry, _manager = await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, GLB_CARD)
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 15)
    journal.add(hass, "test", address=ADDRESS, latitude=LATITUDE, longitude=LONGITUDE)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert set(diagnostics) == {"hub", "subentries", "runtime", "journal"}
    assert diagnostics["runtime"]["session"]["card_uid"] == "**REDACTED**"
    vehicle = next(
        sub["data"] for sub in diagnostics["subentries"] if sub["subentry_type"] == "vehicle"
    )
    assert vehicle["vin"] == "**REDACTED**"
    assert vehicle["cards"][0]["uid"] == "**REDACTED**"
    text = json.dumps(diagnostics, default=str)
    for secret in (GLB_CARD, CARD_LABEL, VIN, ADDRESS, str(LATITUDE), str(LONGITUDE)):
        assert secret not in text
    times = [item["time"] for item in diagnostics["journal"]]
    assert times == sorted(times)
    decided = next(i for i in diagnostics["journal"] if i["event"] == "identification_decided")
    assert decided["data"]["card_uid"] == GLB_CARD[-4:]


# ------------------------------------------------- retention and the limit


async def test_old_entries_are_dropped_when_the_journal_is_loaded(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Entries older than 90 days do not survive loading."""
    now = dt_util.now()
    hass_storage[STORE_KEY_JOURNAL] = {
        "version": 1,
        "minor_version": 1,
        "key": STORE_KEY_JOURNAL,
        "data": {
            "entries": [
                _stored_entry(now - timedelta(days=100), "too_old"),
                _stored_entry(now - timedelta(days=1), "recent"),
            ]
        },
    }

    await _setup(hass)

    events = _events(hass)
    assert "too_old" not in events
    assert events[0] == "recent"


async def test_the_limit_holds_on_load_and_while_running(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Beyond the limit the oldest entries fall out, at loading and when entries are added."""
    now = dt_util.now()
    hass_storage[STORE_KEY_JOURNAL] = {
        "version": 1,
        "minor_version": 1,
        "key": STORE_KEY_JOURNAL,
        "data": {
            "entries": [_stored_entry(now - timedelta(seconds=100 - i), f"e{i}") for i in range(10)]
        },
    }

    with patch("custom_components.ev_charging.journal.JOURNAL_MAX_ENTRIES", 5):
        await _setup(hass)
        assert len(journal.entries(hass)) == 5
        for number in range(20):
            journal.add(hass, f"new{number}")

    assert _events(hass) == [f"new{number}" for number in range(15, 20)]


async def test_old_entries_are_dropped_once_a_day(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The daily pruning drops what has grown older than 90 days while running."""
    await _setup(hass)
    journal.add(hass, "early")

    await _advance(hass, freezer, 91 * 24 * 3600)

    assert "early" not in _events(hass)


async def test_entries_survive_a_restart(hass: HomeAssistant) -> None:
    """The entries are written on unload and read again on the next setup."""
    entry, _manager = await _setup(hass)
    journal.add(hass, "before_restart")

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert journal.entries(hass) == []
    stored = await JournalStore(hass).async_load()
    assert "before_restart" in [item["event"] for item in stored]

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert "before_restart" in _events(hass)


async def test_new_entries_are_written_at_the_persist_interval(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any]
) -> None:
    """Something new is written within the persist interval, nothing is written without it."""
    await _setup(hass)
    journal.add(hass, "tick")

    await _advance(hass, freezer, 121)

    stored = hass_storage[STORE_KEY_JOURNAL]["data"]["entries"]
    assert stored[-1]["event"] == "tick"
    with patch.object(JournalStore, "async_save") as save:
        await _advance(hass, freezer, 121)
    save.assert_not_called()


# -------------------------------------------------- failure stays contained


async def test_a_failing_journal_store_leaves_the_capture_untouched(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A write error of the journal store reaches neither the session nor its record."""
    with patch.object(JournalStore, "async_save", side_effect=OSError("disk full")) as save:
        await _setup(hass)
        await _start_charging(hass, freezer)
        await _set(hass, "sensor.wb_energy_total", "100.1", "kWh")
        await _advance(hass, freezer, 121)
        await _unplug(hass, freezer)
        assert save.called

    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].energy_measured_kwh == 0.1
    assert "session_stored" in _events(hass)


async def test_adding_an_entry_never_raises(hass: HomeAssistant) -> None:
    """A failure inside the journal is swallowed by the caller's call."""
    await _setup(hass)

    with patch.object(journal.Journal, "add", side_effect=RuntimeError("broken")):
        journal.add(hass, "anything", value=1)


# ----------------------------------------------------- a session with error


async def test_a_session_with_a_vehicle_error_journals_the_expected_sequence(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Plug in, charge, a charging error of the vehicle, charge again, unplug."""
    hass.states.async_set(GLB_TRACKER, "home")
    await _setup(hass, vehicles=(_glb(),))
    hass.states.async_set(GLB_TRACKER, "home")
    await hass.async_block_till_done()

    await _set(hass, PLUG, PLUGGED)
    await _set(hass, POWER, "7.0", "kW")
    await _advance(hass, freezer, 2)
    await _advance(hass, freezer, 15)
    await _set(hass, GLB_CHARGE, "4")
    await _advance(hass, freezer, 6)
    await _set(hass, GLB_CHARGE, "0")
    await _advance(hass, freezer, 60)
    await _unplug(hass, freezer)

    assert _events(hass, capture_only=True) == [
        "candidate_created",
        "session_started",
        "phase_opened",
        "session_state_changed",
        "identification_decided",
        "charge_error_reported",
        "phase_closed",
        "session_state_changed",
        "charge_error_ended",
        "phase_opened",
        "session_state_changed",
        "vehicle_session_suppressed",
        "session_state_changed",
        "phase_closed",
        "session_ended",
        "session_state_changed",
        "session_stored",
    ]
    changes = [
        (item["data"]["old"], item["data"]["new"])
        for item in _entries(hass, "session_state_changed")
    ]
    assert changes == [
        ("candidate", "charging"),
        ("charging", "error"),
        ("error", "charging"),
        ("charging", "paused"),
        ("paused", "awaiting_final"),
    ]
    (reported,) = _entries(hass, "charge_error_reported")
    assert reported["vehicle_id"] == "v001"
    assert reported["data"]["source"] == "vehicle"
    (ended,) = _entries(hass, "session_ended")
    assert ended["data"]["reason"] == "unplugged"
    (stored,) = _entries(hass, "session_stored")
    assert stored["data"]["session_id"] == (await _stored(hass))[0].id
    occasions = [item["data"]["occasion"] for item in _entries(hass, "notification_persistent")]
    assert occasions == ["error", "session_end"]
    classes = [
        (item["data"]["role"], item["data"]["class"])
        for item in _entries(hass, "source_class_changed")
        if item.get("vehicle_id") == "v001"
    ]
    assert ("charge_state", "error") in classes


async def test_a_session_without_content_is_journaled_as_discarded(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Plugging in and out without energy leaves the reason in the journal."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 2)
    await _unplug(hass, freezer)

    (discarded,) = _entries(hass, "session_discarded")
    assert discarded["data"]["reason"] == "no_content"
    assert "session_stored" not in _events(hass)


async def test_reads_from_the_register_are_journaled(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Start and end of the sequence and every read with its result."""
    install(monkeypatch, FakeDevice([_card("00000000"), _card(GLB_REPORTED)]))
    await _setup(hass, wallbox=_register_wallbox(), vehicles=(_glb(),))
    await _set(hass, PLUG, PLUGGED)
    for _ in range(4):
        await _advance(hass, freezer, 5)

    reads = [
        (item["event"], item["data"].get("result"))
        for item in journal.entries(hass)
        if item["event"].startswith("read")
    ]
    assert reads == [
        ("read_sequence_started", None),
        ("read", "zero"),
        ("read", "valid"),
        ("read_sequence_ended", "value"),
    ]


# ------------------------------------------------------- repair issues


async def test_repair_issues_are_journaled_only_when_they_change(hass: HomeAssistant) -> None:
    """Creating a standing issue again or deleting an absent one leaves no entry."""
    await _setup(hass)
    arguments = {
        "subentry_id": "sub",
        "subentry_title": "Carport",
        "role_name": "plug_state",
        "raw_value": "odd",
    }

    for _ in range(2):
        problems.check_unknown_mapping_value(hass, found=False, **arguments)
    for _ in range(2):
        problems.check_unknown_mapping_value(hass, found=True, **arguments)

    issue_id = problems.unknown_mapping_value_issue_id("sub", "plug_state")
    for event in (JOURNAL_REPAIR_ISSUE_CREATED, JOURNAL_REPAIR_ISSUE_DELETED):
        ids = [item["data"]["issue_id"] for item in _entries(hass, event)]
        assert ids.count(issue_id) == 1


# -------------------------------------------------------- administration


async def _stored_session(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> str:
    """Charge once and return the id of the stored session, findable by the services."""
    await _start_charging(hass, freezer)
    await _set(hass, "sensor.wb_energy_total", "100.1", "kWh")
    await _unplug(hass, freezer)
    await _touch_year_file(hass, dt_util.now().year)
    return (await _stored(hass, dt_util.now().year))[0].id


async def test_a_service_write_is_journaled_with_field_names_only(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The entry names user, session and changed fields, never the values."""
    await _setup(hass)
    session_id = await _stored_session(hass, freezer)
    admin = MockUser(is_owner=True).add_to_hass(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_SESSION,
        {ATTR_SESSION_ID: session_id, "note": "a private note", "address": ADDRESS},
        blocking=True,
        context=Context(user_id=admin.id),
    )

    (action,) = _entries(hass, JOURNAL_ADMIN_ACTION)
    assert action["data"] == {
        "action": SERVICE_UPDATE_SESSION,
        "user_id": admin.id,
        "session_ids": [session_id],
        "fields": ["address", "note"],
    }
    text = json.dumps(journal.entries(hass))
    assert "a private note" not in text
    assert ADDRESS not in text


async def test_a_rejected_service_call_is_not_journaled(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Only a write that was carried out appears."""
    await _setup(hass)
    user = MockUser(is_owner=False).add_to_hass(hass)

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPDATE_SESSION,
            {ATTR_SESSION_ID: "missing", "note": "x"},
            blocking=True,
            context=Context(user_id=user.id),
        )

    assert _entries(hass, JOURNAL_ADMIN_ACTION) == []


async def test_a_websocket_write_is_journaled_with_field_names_only(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_ws_client: WebSocketGenerator,
    hass_admin_user: MockUser,
) -> None:
    """A write command names its type, the user, the session and the changed fields."""
    await _setup(hass)
    session_id = await _stored_session(hass, freezer)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {"type": "ev_charging/sessions/update", "session_id": session_id, "note": "hidden"}
    )
    response = await client.receive_json()
    assert response["success"]

    (action,) = _entries(hass, JOURNAL_ADMIN_ACTION)
    assert action["data"]["action"] == "ev_charging/sessions/update"
    assert action["data"]["user_id"] == hass_admin_user.id
    assert action["data"]["fields"] == ["note"]
    assert "hidden" not in json.dumps(journal.entries(hass))


async def test_delete_all_data_clears_the_journal_and_keeps_its_own_entry(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """After the deletion the journal holds only the entry of the deletion."""
    await _setup(hass)
    await _stored_session(hass, freezer)
    admin = MockUser(is_owner=True).add_to_hass(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_DELETE_ALL_DATA,
        {ATTR_CONFIRM: True},
        blocking=True,
        context=Context(user_id=admin.id),
    )

    entries = journal.entries(hass)
    assert len(entries) == 1
    assert entries[0]["event"] == JOURNAL_ADMIN_ACTION
    assert entries[0]["data"]["action"] == SERVICE_DELETE_ALL_DATA
    assert entries[0]["data"]["user_id"] == admin.id


# ------------------------------------------------------------- removal


async def test_removing_the_integration_discards_journal_and_runtime_state(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any]
) -> None:
    """Both stores are gone after removal; the stored sessions stay."""
    entry, _manager = await _setup(hass)
    await _stored_session(hass, freezer)
    await _set(hass, PLUG, PLUGGED)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert STORE_KEY_JOURNAL in hass_storage
    assert STORE_KEY_RUNTIME in hass_storage

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert STORE_KEY_JOURNAL not in hass_storage
    assert STORE_KEY_RUNTIME not in hass_storage
    assert len(await _stored(hass)) == 1
