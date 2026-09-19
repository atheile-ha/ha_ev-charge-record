"""Tests for the read-only WebSocket commands of the panel and the cards."""

from __future__ import annotations

import logging
import os
from typing import Any

import pytest
from custom_components.ev_charging import websocket
from custom_components.ev_charging.const import (
    DOMAIN,
    SUBENTRY_TYPE_VEHICLE,
    TITLE,
    store_key_sessions,
)
from custom_components.ev_charging.models import Card, Session, Vehicle
from custom_components.ev_charging.store import SessionYearStore
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

TIME_ZONE = "Europe/Berlin"


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Give this module's hass a private config dir instead of the shared default.

    The year files are real files placed directly in the storage directory,
    because the list of available years is read from disk.
    """
    return hass_tmp_config_dir


@pytest.fixture(autouse=True)
async def _setup(hass: HomeAssistant) -> None:
    """Use a fixed time zone and register the commands."""
    await hass.config.async_set_time_zone(TIME_ZONE)
    websocket.async_setup_websocket(hass)


def _session(session_id: str, plug_start: str, **fields: Any) -> Session:
    return Session(
        id=session_id,
        location=fields.pop("location", "home"),
        plug_start=plug_start,
        identification_source=fields.pop("identification_source", "manual"),
        **fields,
    )


async def _store(hass: HomeAssistant, year: int, sessions: list[Session]) -> None:
    """Save the sessions and create the file the year scan looks for."""
    await SessionYearStore(hass, year).async_save(sessions)

    def _touch() -> None:
        storage_dir = hass.config.path(".storage")
        os.makedirs(storage_dir, exist_ok=True)
        open(os.path.join(storage_dir, store_key_sessions(year)), "a", encoding="utf-8").close()

    await hass.async_add_executor_job(_touch)


async def _call(client: Any, command: str, **params: Any) -> dict[str, Any]:
    await client.send_json_auto_id({"type": f"ev_charging/{command}", **params})
    return await client.receive_json()


async def test_list_returns_the_sessions_of_one_month_newest_first(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A month's list holds only that month, ordered by plug_start descending."""
    await _store(
        hass,
        2026,
        [
            _session("a", "2026-05-03T08:00:00+02:00"),
            _session("b", "2026-05-20T08:00:00+02:00"),
            _session("c", "2026-06-01T08:00:00+02:00"),
        ],
    )
    client = await hass_ws_client(hass)

    response = await _call(client, "sessions/list", year=2026, month=5)

    assert response["success"]
    assert [s["id"] for s in response["result"]["sessions"]] == ["b", "a"]


async def test_month_follows_plug_start_in_local_time(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A session belongs to the month of its local plug_start, not its UTC month or its end."""
    await _store(
        hass,
        2026,
        [
            # 23:30 UTC on 30 September is 01:30 on 1 October in Berlin.
            _session("utc_september", "2026-09-30T23:30:00+00:00"),
            # Starts on 31 December local time and ends in the next year.
            _session(
                "new_year",
                "2026-12-31T23:30:00+01:00",
                plug_end="2027-01-01T02:00:00+01:00",
            ),
        ],
    )
    client = await hass_ws_client(hass)

    october = await _call(client, "sessions/list", year=2026, month=10)
    september = await _call(client, "sessions/list", year=2026, month=9)
    december = await _call(client, "sessions/list", year=2026, month=12)
    stats = await _call(client, "sessions/stats", year=2026)

    assert [s["id"] for s in october["result"]["sessions"]] == ["utc_september"]
    assert september["result"]["sessions"] == []
    assert [s["id"] for s in december["result"]["sessions"]] == ["new_year"]
    counts = {m["month"]: m["count"] for m in stats["result"]["months"]}
    assert counts[10] == 1
    assert counts[9] == 0
    assert counts[12] == 1


async def test_list_without_year_returns_the_newest_across_years(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Without a year the newest sessions of all years are returned, up to the limit."""
    await _store(hass, 2025, [_session("old", "2025-12-30T08:00:00+01:00")])
    await _store(
        hass,
        2026,
        [
            _session("mid", "2026-02-01T08:00:00+01:00"),
            _session("new", "2026-03-01T08:00:00+01:00"),
        ],
    )
    client = await hass_ws_client(hass)

    response = await _call(client, "sessions/list", limit=2)

    assert [s["id"] for s in response["result"]["sessions"]] == ["new", "mid"]


async def test_list_rejects_a_month_without_a_year(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A month alone is not a period."""
    client = await hass_ws_client(hass)

    response = await _call(client, "sessions/list", month=5)

    assert not response["success"]
    assert response["error"]["code"] == "invalid_format"


async def test_list_rejects_out_of_range_values(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Month, year and limit are validated."""
    client = await hass_ws_client(hass)

    assert not (await _call(client, "sessions/list", year=2026, month=13))["success"]
    assert not (await _call(client, "sessions/list", year=26))["success"]
    assert not (await _call(client, "sessions/list", limit=0))["success"]


async def test_unassigned_sessions_are_listed_and_counted(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A session without a vehicle is neither hidden nor left out of the sums."""
    await _store(
        hass,
        2026,
        [
            _session(
                "assigned",
                "2026-05-03T08:00:00+02:00",
                vehicle_id="v001",
                energy_kwh=10.0,
                cost=2.5,
                charge_duration_min=60.0,
            ),
            _session(
                "unassigned",
                "2026-05-04T08:00:00+02:00",
                identification_source="unresolved",
                energy_kwh=20.0,
                cost=5.0,
                charge_duration_min=120.0,
            ),
        ],
    )
    client = await hass_ws_client(hass)

    listing = await _call(client, "sessions/list", year=2026, month=5)
    stats = await _call(client, "sessions/stats", year=2026)

    by_id = {s["id"]: s for s in listing["result"]["sessions"]}
    assert by_id["unassigned"]["vehicle_id"] is None
    may = stats["result"]["months"][4]
    assert may["count"] == 2
    assert may["energy_kwh"] == 30.0
    assert may["cost"] == 7.5
    assert may["charge_duration_min"] == 180.0


async def test_stats_sums_present_values_and_flags_estimates(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A missing value adds nothing; a month with an estimated energy says so."""
    await _store(
        hass,
        2026,
        [
            _session(
                "measured",
                "2026-05-03T08:00:00+02:00",
                energy_measured_kwh=10.0,
                energy_kwh=10.0,
                cost=None,
            ),
            _session("missing", "2026-05-04T08:00:00+02:00", energy_kwh=None, cost=1.0),
            _session(
                "estimated",
                "2026-06-04T08:00:00+02:00",
                energy_estimated_kwh=5.0,
                energy_kwh=5.0,
            ),
        ],
    )
    client = await hass_ws_client(hass)

    stats = (await _call(client, "sessions/stats", year=2026))["result"]

    may, june = stats["months"][4], stats["months"][5]
    assert (may["count"], may["energy_kwh"], may["cost"]) == (2, 10.0, 1.0)
    assert may["energy_is_estimate"] is False
    assert june["energy_is_estimate"] is True
    assert stats["years"] == [2026]
    assert len(stats["months"]) == 12


async def test_estimate_flag_is_part_of_each_listed_session(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """The panel marks a session's energy with a tilde only when it is an estimate."""
    await _store(
        hass,
        2026,
        [
            _session(
                "measured", "2026-05-03T08:00:00+02:00", energy_measured_kwh=1.0, energy_kwh=1.0
            ),
            _session(
                "estimated", "2026-05-04T08:00:00+02:00", energy_estimated_kwh=2.0, energy_kwh=2.0
            ),
        ],
    )
    client = await hass_ws_client(hass)

    sessions = (await _call(client, "sessions/list", year=2026))["result"]["sessions"]

    assert {s["id"]: s["energy_is_estimate"] for s in sessions} == {
        "measured": False,
        "estimated": True,
    }


async def test_open_returns_sessions_that_wait_for_values(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Sessions with status followup_open or open fields are returned, across all years."""
    await _store(
        hass,
        2025,
        [_session("old_open", "2025-12-01T08:00:00+01:00", status="followup_open")],
    )
    await _store(
        hass,
        2026,
        [
            _session("complete", "2026-01-01T08:00:00+01:00"),
            _session("with_field", "2026-02-01T08:00:00+01:00", open_fields=("soc_end",)),
            _session("flagged", "2026-03-01T08:00:00+01:00", status="flagged"),
        ],
    )
    client = await hass_ws_client(hass)

    response = await _call(client, "sessions/open")

    assert [s["id"] for s in response["result"]["sessions"]] == ["with_field", "old_open"]


async def test_vehicles_list_excludes_identifiers(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Vehicles come from the configuration, without VIN and cards."""
    vehicle = Vehicle(
        id="v001",
        name="Car One",
        active=False,
        vin="TESTVIN0000000001",
        cards=(Card(uid="AABBCCDD", label="Blue card"),),
        manufacturer="Acme",
        model="One",
    )
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
    client = await hass_ws_client(hass)

    response = await _call(client, "vehicles/list")

    assert response["result"]["vehicles"] == [
        {
            "id": "v001",
            "name": "Car One",
            "active": False,
            "is_guest": False,
            "manufacturer": "Acme",
            "model": "One",
        }
    ]


@pytest.mark.parametrize(
    ("command", "params"),
    [
        ("sessions/list", {"year": 2026, "month": 5}),
        ("sessions/stats", {"year": 2026}),
        ("sessions/open", {}),
        ("vehicles/list", {}),
    ],
)
async def test_every_command_answers_a_non_administrator(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    command: str,
    params: dict[str, Any],
) -> None:
    """All read commands work for a user without administrator rights."""
    await _store(hass, 2026, [_session("a", "2026-05-03T08:00:00+02:00", status="followup_open")])
    client = await hass_ws_client(hass, hass_read_only_access_token)

    response = await _call(client, command, **params)

    assert response["success"], response


async def test_reading_does_not_log_identifiers_at_info(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, caplog: pytest.LogCaptureFixture
) -> None:
    """Card, address and coordinates reach the panel but never the log at INFO."""
    await _store(
        hass,
        2026,
        [
            _session(
                "a",
                "2026-05-03T08:00:00+02:00",
                card_uid="AABBCCDD",
                card_label="Blue card",
                address="1 Test Street, Testville",
                latitude=50.123456,
                longitude=8.654321,
            )
        ],
    )
    client = await hass_ws_client(hass)
    caplog.clear()

    response = await _call(client, "sessions/list", year=2026, month=5)

    assert response["result"]["sessions"][0]["card_uid"] == "AABBCCDD"
    logged = " ".join(
        record.getMessage() for record in caplog.records if record.levelno >= logging.INFO
    )
    for identifier in ("AABBCCDD", "Blue card", "Test Street", "50.123456", "8.654321"):
        assert identifier not in logged
