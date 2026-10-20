"""Tests for error detection, the problem entity and the notifications."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from custom_components.ev_charging.const import DOMAIN, SESSION_STATE_ERROR, TITLE
from custom_components.ev_charging.models import HubSettings, NotifyTarget
from custom_components.ev_charging.notify import format_number, persistent_notification_id
from custom_components.ev_charging.store import RuntimeStore
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from tests.test_session_manager import (
    CARD,
    CHARGING_DC,
    CONNECTED_IDLE,
    DISCONNECTED,
    ERROR,
    ERROR_CODE,
    GLB_CARD,
    GLB_CHARGE,
    NEUTRAL_MISSING,
    PLUG,
    PLUGGED,
    POWER,
    TOTAL,
    _advance,
    _external_block,
    _glb,
    _glb_ext,
    _hub,
    _issue,
    _set,
    _setup,
    _start_charging,
    _stored,
    _unplug,
)

PROBLEM = "binary_sensor.ev_charging_problem"
SPEAKER = "notify.speaker"
PHONE = "mobile_app_phone"

_CREATE = "custom_components.ev_charging.notify.persistent_notification.async_create"


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Give the test a private config dir: the years with data are read from disk."""
    return hass_tmp_config_dir


@pytest.fixture(autouse=True)
async def _time_zone(hass: HomeAssistant) -> None:
    """Use a fixed time zone."""
    await hass.config.async_set_time_zone("Europe/Berlin")


@pytest.fixture
def persistent() -> Iterator[MagicMock]:
    """Capture the persistent notifications."""
    with patch(_CREATE) as create:
        yield create


def _targets(hass: HomeAssistant) -> tuple[list[ServiceCall], list[ServiceCall]]:
    """Provide a notify entity and a classic notify service as targets."""
    hass.states.async_set(SPEAKER, "unknown")
    return (
        async_mock_service(hass, "notify", "send_message"),
        async_mock_service(hass, "notify", PHONE),
    )


def _hub_with_targets(**overrides: Any) -> dict[str, Any]:
    return _hub(
        notify_target_1=NotifyTarget(kind="entity", target=SPEAKER),
        notify_target_2=NotifyTarget(kind="service", target=f"notify.{PHONE}"),
        **overrides,
    )


def _ids(persistent: MagicMock) -> list[str]:
    return [call.kwargs["notification_id"] for call in persistent.call_args_list]


def _titles(persistent: MagicMock) -> list[str]:
    return [call.kwargs["title"] for call in persistent.call_args_list]


# ---------------------------------------------------------------- formatting


def test_numbers_follow_the_decimal_separator_of_the_language() -> None:
    assert format_number(12.3456, 3, ",") == "12,346"
    assert format_number(4.5, 2, ".") == "4.50"
    assert format_number(85.0, 0, ",") == "85"


def test_persistent_notification_ids_count_from_one() -> None:
    assert [persistent_notification_id(slot) for slot in range(5)] == [
        "ev_charging_1",
        "ev_charging_2",
        "ev_charging_3",
        "ev_charging_4",
        "ev_charging_5",
    ]


def test_hub_settings_keep_the_kind_of_each_target() -> None:
    settings = HubSettings(
        notify_target_1=NotifyTarget(kind="service", target="notify.mobile_app_phone"),
        notify_on_followup=True,
    )

    restored = HubSettings.from_dict(settings.to_dict())

    assert restored == settings
    assert restored.notify_target_1 == NotifyTarget(
        kind="service", target="notify.mobile_app_phone"
    )
    assert restored.notify_target_2 is None


def test_an_unreadable_target_is_no_target() -> None:
    assert NotifyTarget.from_dict({"kind": "sms", "target": "notify.x"}) is None
    assert NotifyTarget.from_dict({"kind": "entity", "target": ""}) is None
    assert NotifyTarget.from_dict(None) is None


# -------------------------------------------------------------- wallbox error


async def test_a_wallbox_error_switches_the_problem_entity_and_keeps_the_session_open(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """The wallbox error is reported once it held for 5 s; the session stays open."""
    _entry, manager = await _setup(hass)
    await _start_charging(hass, freezer)
    assert hass.states.get(PROBLEM).state == "off"

    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 4)
    assert hass.states.get(PROBLEM).state == "off"
    await _advance(hass, freezer, 2)

    state = hass.states.get(PROBLEM)
    assert state.state == "on"
    assert state.attributes["device_class"] == "problem"
    assert state.attributes["source"] == "wallbox"
    assert state.attributes["vehicle_id"] is None
    assert hass.states.get("sensor.carport_wallbox_state").state == SESSION_STATE_ERROR
    assert await _stored(hass) == []
    assert _titles(persistent) == ["Charging error"]
    message = persistent.call_args.args[1]
    assert "Carport" in message
    assert "error" in message
    block = manager.live_blocks()[0]
    assert block["charge_error"] is True
    assert block["charge_error_source"] == "wallbox"

    await _set(hass, ERROR, "charging")
    assert hass.states.get(PROBLEM).state == "off"
    assert hass.states.get(PROBLEM).attributes["source"] is None
    block = manager.live_blocks()[0]
    assert block["charge_error"] is True
    assert block["charge_error_source"] is None


@pytest.mark.parametrize("raw", ["charging_is_temporarily_interrupted", "undefined"])
async def test_an_interruption_or_a_neutral_value_is_no_wallbox_error(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock, raw: str
) -> None:
    """Code 5 of the KEBA charging state and its neutral value are no error."""
    await _setup(hass)
    await _start_charging(hass, freezer)

    await _set(hass, ERROR, raw)
    await _advance(hass, freezer, 30)

    assert hass.states.get(PROBLEM).state == "off"
    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
    assert persistent.call_count == 0


async def test_a_wallbox_error_without_a_session_is_reported(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """A reported error counts without a session and creates none."""
    _entry, manager = await _setup(hass)

    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)

    assert hass.states.get(PROBLEM).state == "on"
    assert manager.live_blocks()[0]["charge_error_source"] == "wallbox"
    assert hass.states.get("sensor.carport_wallbox_state").state == "idle"
    assert _titles(persistent) == ["Charging error"]


async def test_a_session_begun_during_a_wallbox_error_goes_to_the_error_state(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """A session confirmed while the error is reported enters the error state at once."""
    await _setup(hass)
    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)

    await _start_charging(hass, freezer)

    assert hass.states.get("sensor.carport_wallbox_state").state == SESSION_STATE_ERROR
    assert _titles(persistent) == ["Charging error"]


async def test_a_lasting_error_is_not_reported_again_after_a_restart(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """An error reported before a restart stands without a second notification."""
    entry, _ = await _setup(hass)
    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)
    assert persistent.call_count == 1

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    await _advance(hass, freezer, 10)

    assert hass.states.get(PROBLEM).state == "on"
    assert persistent.call_count == 1


async def test_a_session_stored_in_error_without_a_reported_error_leaves_the_error_state(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """A session restored in the error state follows the source, even without a stored error."""
    entry, _ = await _setup(hass)
    await _start_charging(hass, freezer)
    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    stored = await RuntimeStore(hass).async_load()
    assert stored["session"]["state"] == SESSION_STATE_ERROR
    stored.pop("problems")
    await RuntimeStore(hass).async_save(stored)

    hass.states.async_set(ERROR, "charging")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
    assert hass.states.get(PROBLEM).state == "off"


# -------------------------------------------------------------- vehicle error


async def test_a_vehicle_error_during_an_external_session_is_reported_and_keeps_it_open(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """Code 4 of the Mercedes charging state is a vehicle error, also away from home."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 60)

    await _set(hass, GLB_CHARGE, ERROR_CODE)
    await _advance(hass, freezer, 2)
    assert _external_block(manager, "v001")["state"] == "charging"
    await _advance(hass, freezer, 4)

    state = hass.states.get(PROBLEM)
    assert state.state == "on"
    assert state.attributes["source"] == "vehicle"
    assert state.attributes["vehicle_id"] == "v001"
    block = _external_block(manager, "v001")
    assert block["state"] == SESSION_STATE_ERROR
    assert block["charge_error_source"] == "vehicle"
    assert manager.live_blocks()[0]["charge_error_source"] is None
    assert await _stored(hass) == []
    assert _titles(persistent) == ["Charging error"]
    assert "GLB" in persistent.call_args.args[1]

    await _set(hass, GLB_CHARGE, CHARGING_DC)
    assert hass.states.get(PROBLEM).state == "off"
    assert _external_block(manager, "v001")["state"] == "charging"


async def test_the_neutral_error_value_of_the_vehicle_is_no_error(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """The Mercedes value error, an absent attribute, is neutral and reports nothing."""
    _entry, manager = await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, GLB_CHARGE, CHARGING_DC)

    await _set(hass, GLB_CHARGE, NEUTRAL_MISSING)
    await _advance(hass, freezer, 30)

    assert hass.states.get(PROBLEM).state == "off"
    assert _external_block(manager, "v001")["state"] == "charging"
    assert persistent.call_count == 0


async def test_a_vehicle_error_puts_the_wallbox_session_of_that_vehicle_in_error(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """The wallbox session that names the vehicle follows its error and stays open."""
    _entry, manager = await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, GLB_CARD)
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 20)
    assert hass.states.get("sensor.carport_active_vehicle").state == "GLB"

    await _set(hass, GLB_CHARGE, ERROR_CODE)
    await _advance(hass, freezer, 6)

    assert hass.states.get("sensor.carport_wallbox_state").state == SESSION_STATE_ERROR
    assert hass.states.get(PROBLEM).attributes["source"] == "vehicle"
    assert manager.live_blocks()[0]["charge_error_source"] == "vehicle"

    await _set(hass, GLB_CHARGE, CONNECTED_IDLE)
    assert hass.states.get(PROBLEM).state == "off"
    assert hass.states.get("sensor.carport_wallbox_state").state in ("charging", "paused")
    await _unplug(hass, freezer)
    sessions = await _stored(hass)
    assert len(sessions) == 1
    assert sessions[0].charge_error is True


async def test_the_latest_error_names_the_source(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """With two errors reported, the newer one sets the attributes, the older one follows."""
    await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)
    await _set(hass, GLB_CHARGE, ERROR_CODE)
    await _advance(hass, freezer, 6)

    assert hass.states.get(PROBLEM).attributes["source"] == "vehicle"

    await _set(hass, GLB_CHARGE, DISCONNECTED)
    state = hass.states.get(PROBLEM)
    assert state.state == "on"
    assert state.attributes["source"] == "wallbox"


# ------------------------------------------------------- persistent rotation


async def test_persistent_notifications_rotate_through_five_ids_across_a_restart(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """The sixth notification takes the first id again; the position survives a restart."""
    entry, _ = await _setup(hass)
    for _ in range(3):
        await _set(hass, ERROR, "error")
        await _advance(hass, freezer, 6)
        await _set(hass, ERROR, "charging")

    assert (await RuntimeStore(hass).async_load())["notification_slot"] == 3
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    for _ in range(3):
        await _set(hass, ERROR, "error")
        await _advance(hass, freezer, 6)
        await _set(hass, ERROR, "charging")

    assert _ids(persistent) == [
        "ev_charging_1",
        "ev_charging_2",
        "ev_charging_3",
        "ev_charging_4",
        "ev_charging_5",
        "ev_charging_1",
    ]


async def test_persistent_notifications_can_be_switched_off(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """Without persistent notifications nothing is created and no id is used."""
    await _setup(hass, hub=_hub(persistent_enabled=False))

    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)

    assert persistent.call_count == 0
    assert (await RuntimeStore(hass).async_load())["notification_slot"] == 0


# ------------------------------------------------------------------- targets


async def test_both_target_forms_receive_the_error(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """A notify entity is sent to through send_message, a classic service by its own name."""
    entity_calls, service_calls = _targets(hass)
    await _setup(hass, hub=_hub_with_targets())

    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)

    assert len(entity_calls) == 1
    assert entity_calls[0].data["entity_id"] == SPEAKER
    assert entity_calls[0].data["title"] == "Charging error"
    assert len(service_calls) == 1
    assert service_calls[0].data["title"] == "Charging error"
    assert "Carport" in service_calls[0].data["message"]
    assert persistent.call_count == 1


async def test_each_occasion_of_the_targets_can_be_switched_off(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """With the error occasion off, the targets get nothing; the persistent one still comes."""
    entity_calls, service_calls = _targets(hass)
    await _setup(hass, hub=_hub_with_targets(notify_on_error=False))

    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)

    assert entity_calls == []
    assert service_calls == []
    assert persistent.call_count == 1


async def test_a_missing_target_raises_an_issue_and_the_other_is_still_served(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """A removed notify entity becomes a repair issue; the service target keeps receiving."""
    entity_calls, service_calls = _targets(hass)
    await _setup(hass, hub=_hub_with_targets())
    assert _issue(hass, "notify_target_missing_1") is None

    hass.states.async_remove(SPEAKER)
    await hass.async_block_till_done()
    issue = _issue(hass, "notify_target_missing_1")
    assert issue is not None
    assert issue.translation_placeholders == {"target": SPEAKER}

    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)
    assert entity_calls == []
    assert len(service_calls) == 1

    await _set(hass, SPEAKER, "unknown")
    assert _issue(hass, "notify_target_missing_1") is None


async def test_a_removed_notify_service_raises_an_issue(
    hass: HomeAssistant, persistent: MagicMock
) -> None:
    """A classic notify service that disappears becomes a repair issue."""
    _targets(hass)
    await _setup(hass, hub=_hub_with_targets())

    hass.services.async_remove("notify", PHONE)
    await hass.async_block_till_done()

    issue = _issue(hass, "notify_target_missing_2")
    assert issue is not None
    assert issue.translation_placeholders == {"target": f"notify.{PHONE}"}


async def test_a_target_missing_at_startup_raises_an_issue(
    hass: HomeAssistant, persistent: MagicMock
) -> None:
    """A configured target that does not exist once Home Assistant runs is reported."""
    async_mock_service(hass, "notify", PHONE)
    await _setup(hass, hub=_hub_with_targets())

    assert _issue(hass, "notify_target_missing_1") is not None
    assert _issue(hass, "notify_target_missing_2") is None


# ------------------------------------------------------------------ sessions


async def test_a_finished_wallbox_session_is_summarized(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """The summary names vehicle, location, energy, split, cost and the net charging time."""
    entity_calls, service_calls = _targets(hass)
    await _setup(hass, vehicles=(_glb(),), hub=_hub_with_targets())
    await _set(hass, CARD, GLB_CARD)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 20)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")

    await _unplug(hass, freezer)

    assert _titles(persistent) == ["Charging finished"]
    message = persistent.call_args.args[1]
    assert message.splitlines()[0] == "GLB, home (wallbox)"
    assert "Energy: 1.000 kWh" in message
    assert "Grid: " in message
    assert "Cost: " in message
    assert "Net charging time:" in message
    assert len(entity_calls) == 1
    assert entity_calls[0].data["title"] == "Charging finished"
    assert len(service_calls) == 1


async def test_the_summary_uses_the_number_format_of_the_language(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """In German the summary carries a decimal comma."""
    hass.config.language = "de"
    await _setup(hass, vehicles=(_glb(),))
    await _set(hass, CARD, GLB_CARD)
    await _start_charging(hass, freezer, power_kw=6.0)
    await _advance(hass, freezer, 620)
    await _set(hass, TOTAL, "101.5", "kWh")

    await _unplug(hass, freezer)

    assert _titles(persistent) == ["Ladevorgang beendet"]
    message = persistent.call_args.args[1]
    assert message.splitlines()[0] == "GLB, zu Hause (Wallbox)"
    assert "Energie: 1,500 kWh" in message


async def test_a_session_without_content_sends_nothing(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """A discarded session is neither stored nor reported."""
    await _setup(hass)
    await _set(hass, PLUG, PLUGGED)
    await _advance(hass, freezer, 600)

    await _unplug(hass, freezer)

    assert persistent.call_count == 0


async def test_an_open_followup_is_reported_to_the_targets_when_switched_on(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """An unassigned session waits for values; the targets learn of it only when asked to."""
    entity_calls, _service_calls = _targets(hass)
    await _setup(hass, hub=_hub_with_targets(notify_on_followup=True, notify_on_session_end=False))
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 600)
    await _set(hass, TOTAL, "101.0", "kWh")

    await _unplug(hass, freezer)

    assert [call.data["title"] for call in entity_calls] == ["Follow-up open"]
    assert "Unassigned vehicle" in entity_calls[0].data["message"]
    assert "follow-up" in persistent.call_args.args[1]


async def test_an_external_session_is_reported_at_its_start_and_its_end(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """The start goes to the targets only; the end to the targets and as persistent summary."""
    entity_calls, _service_calls = _targets(hass)
    await _setup(hass, vehicles=(_glb_ext(),), hub=_hub_with_targets())

    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await hass.async_block_till_done()
    assert [call.data["title"] for call in entity_calls] == ["External charging started"]
    assert "State of charge: 40 %" in entity_calls[0].data["message"]
    assert persistent.call_count == 0

    await _advance(hass, freezer, 1800)
    await _set(hass, GLB_CHARGE, DISCONNECTED)
    await _advance(hass, freezer, 1)

    assert [call.data["title"] for call in entity_calls] == [
        "External charging started",
        "External charging finished",
    ]
    assert _titles(persistent) == ["External charging finished"]
    assert persistent.call_args.args[1].splitlines()[0] == "GLB, external"


async def test_a_session_closed_after_the_timeout_is_reported(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """The close after 12 hours without a usable plug state comes as its own notification."""
    await _setup(hass)
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 600)
    await _set(hass, PLUG, "unavailable")

    await _advance(hass, freezer, 12 * 3600 + 5)

    assert "Charging session closed" in _titles(persistent)
    assert "Charging finished" not in _titles(persistent)
    message = persistent.call_args_list[_titles(persistent).index("Charging session closed")]
    assert "12 hours" in message.args[1]


async def test_an_external_session_closed_after_the_timeout_is_reported(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """A vehicle session closed because its charge state stayed unavailable is reported."""
    await _setup(hass, vehicles=(_glb_ext(),))
    await _set(hass, GLB_CHARGE, CHARGING_DC)
    await _advance(hass, freezer, 60)
    await _set(hass, GLB_CHARGE, "unavailable")

    await _advance(hass, freezer, 12 * 3600 + 5)

    assert _titles(persistent) == ["Charging session closed"]
    assert "GLB" in persistent.call_args.args[1]


async def test_power_still_drives_a_session_in_error(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, persistent: MagicMock
) -> None:
    """Power returning during a reported error opens a new phase; nothing ends the session."""
    await _setup(hass)
    await _start_charging(hass, freezer)
    await _set(hass, ERROR, "error")
    await _advance(hass, freezer, 6)
    await _set(hass, POWER, "0", "kW")
    await _set(hass, POWER, "6.0", "kW")

    assert hass.states.get("sensor.carport_wallbox_state").state == "charging"
    assert hass.states.get(PROBLEM).state == "on"
    assert await _stored(hass) == []


# --------------------------------------------------------------- config flow


async def _hub_entry(hass: HomeAssistant, data: dict[str, Any] | None = None) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=data or {"wallbox_seq": 0, "vehicle_seq": 0, **HubSettings().to_dict()},
        version=6,
        minor_version=1,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


_RECONFIGURE_BASE = {
    "update_interval_s": 30,
    "solar_valuation": "feed_in_tariff",
    "geocoding_enabled": False,
    "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
    "estimate_uncertain_threshold_pct": 5,
    "grid_power_inverted": False,
}


def _target_options(result: dict[str, Any]) -> list[str]:
    schema = result["data_schema"].schema
    section = next(value for key, value in schema.items() if str(key) == "notifications")
    for key, selector in section.schema.schema.items():
        if str(key) == "notify_target_1":
            return [option["value"] for option in selector.config["options"]]
    raise AssertionError("no target field")


async def test_the_dialog_offers_notify_entities_and_services_together(
    hass: HomeAssistant,
) -> None:
    """Both target forms appear in one list; send_message itself is not a target."""
    _targets(hass)
    entry = await _hub_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )

    options = _target_options(result)
    assert f"entity:{SPEAKER}" in options
    assert f"service:notify.{PHONE}" in options
    assert "service:notify.send_message" not in options


async def test_the_dialog_stores_targets_with_their_form_and_the_switches(
    hass: HomeAssistant,
) -> None:
    """The chosen targets keep their form; every occasion is stored as set."""
    _targets(hass)
    entry = await _hub_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            **_RECONFIGURE_BASE,
            "notifications": {
                "persistent_enabled": True,
                "persistent_on_session_end": False,
                "persistent_on_error": True,
                "notify_target_1": f"service:notify.{PHONE}",
                "notify_target_2": f"entity:{SPEAKER}",
                "notify_on_session_end": True,
                "notify_on_external_start": False,
                "notify_on_external_end": True,
                "notify_on_error": True,
                "notify_on_followup": True,
            },
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert entry.data["notify_target_1"] == {"kind": "service", "target": f"notify.{PHONE}"}
    assert entry.data["notify_target_2"] == {"kind": "entity", "target": SPEAKER}
    assert entry.data["persistent_on_session_end"] is False
    assert entry.data["notify_on_external_start"] is False
    assert entry.data["notify_on_followup"] is True


async def test_the_dialog_rejects_the_same_target_twice(hass: HomeAssistant) -> None:
    _targets(hass)
    entry = await _hub_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            **_RECONFIGURE_BASE,
            "notifications": {
                "notify_target_1": f"entity:{SPEAKER}",
                "notify_target_2": f"entity:{SPEAKER}",
            },
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "notify_target_duplicate"}


async def test_a_configured_target_that_is_gone_stays_selectable(hass: HomeAssistant) -> None:
    """Saving the dialog never drops a target only because it does not exist right now."""
    data = {
        "wallbox_seq": 0,
        "vehicle_seq": 0,
        **HubSettings(notify_target_1=NotifyTarget(kind="service", target="notify.gone")).to_dict(),
    }
    entry = await _hub_entry(hass, data)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )

    assert "service:notify.gone" in _target_options(result)


async def test_an_entry_of_version_5_gains_the_notification_settings(hass: HomeAssistant) -> None:
    """The migration adds every notification setting at its default, once."""
    data = {"wallbox_seq": 0, "vehicle_seq": 0, **HubSettings().to_dict()}
    for key in list(data):
        if key.startswith(("persistent_", "notify_")):
            del data[key]
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data=data, version=5, minor_version=1)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 6
    assert entry.data["persistent_enabled"] is True
    assert entry.data["notify_on_followup"] is False
    assert entry.data["notify_target_1"] is None
