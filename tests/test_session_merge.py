"""Tests for merging stored sessions through the manager, the service and the
WebSocket command."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest
from custom_components.ev_charging import session_manager, websocket
from custom_components.ev_charging.const import (
    ATTR_CONFIRM,
    ATTR_ODOMETER_KM,
    ATTR_SESSION_IDS,
    DOMAIN,
    SERVICE_MERGE_SESSIONS,
    store_key_sessions,
)
from custom_components.ev_charging.models import Session
from custom_components.ev_charging.store import SessionYearStore
from homeassistant.components import websocket_api
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from pytest_homeassistant_custom_component.common import MockUser
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from tests.test_services import _setup_hub


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Give this module's hass a private config dir: the year scan reads real files."""
    return hass_tmp_config_dir


@pytest.fixture(autouse=True)
async def _time_zone(hass: HomeAssistant) -> None:
    await hass.config.async_set_time_zone("Europe/Berlin")


def _session(session_id: str, start: str, end: str, **overrides: Any) -> Session:
    fields: dict[str, Any] = {
        "id": session_id,
        "location": "home",
        "plug_start": start,
        "plug_end": end,
        "identification_source": "rfid",
        "vehicle_id": "v002",
        "wallbox_id": "wb001",
        "card_uid": "SYNTHETIC01",
        "charge_type": "ac",
        "charge_type_source": "wallbox_config",
        "odometer_km": 7699.0,
        "charge_duration_min": 30.0,
        "energy_measured_kwh": 5.0,
        "energy_kwh": 5.0,
        "energy_grid_kwh": 1.0,
        "energy_solar_kwh": 4.0,
        "cost": 0.5,
    }
    fields.update(overrides)
    return Session(**fields)


FIRST = _session("s1", "2026-09-05T18:00:00+02:00", "2026-09-05T18:40:00+02:00")
SECOND = _session("s2", "2026-09-05T19:00:00+02:00", "2026-09-05T19:40:00+02:00")
OTHER = _session("s3", "2026-09-07T08:00:00+02:00", "2026-09-07T09:00:00+02:00")


async def _store(hass: HomeAssistant, year: int, sessions: list[Session]) -> None:
    await SessionYearStore(hass, year).async_save(sessions)

    def _touch() -> None:
        storage_dir = hass.config.path(".storage")
        os.makedirs(storage_dir, exist_ok=True)
        open(os.path.join(storage_dir, store_key_sessions(year)), "a", encoding="utf-8").close()

    await hass.async_add_executor_job(_touch)


async def _stored_ids(hass: HomeAssistant, year: int = 2026) -> list[str]:
    return [session.id for session in await SessionYearStore(hass, year).async_load()]


# -------------------------------------------------------------------- manager


async def test_merge_replaces_the_sources_in_one_step(hass: HomeAssistant) -> None:
    await _store(hass, 2026, [FIRST, SECOND, OTHER])

    merged = await session_manager.async_merge_sessions(hass, ["s2", "s1"], {})

    assert merged.id == "s1"
    assert await _stored_ids(hass) == ["s1", "s3"]
    stored = (await SessionYearStore(hass, 2026).async_load())[0]
    assert stored == merged
    assert stored.energy_measured_kwh == 10.0
    assert stored.energy_kwh == 10.0
    assert stored.cost == 1.0
    assert stored.plug_end == "2026-09-05T19:40:00+02:00"
    assert stored.charge_duration_min == 60.0


async def test_dry_run_writes_nothing(hass: HomeAssistant) -> None:
    await _store(hass, 2026, [FIRST, SECOND])

    preview = await session_manager.async_merge_sessions(hass, ["s1", "s2"], {}, dry_run=True)

    assert preview.energy_kwh == 10.0
    assert await _stored_ids(hass) == ["s1", "s2"]


async def test_a_rejected_merge_leaves_the_store_unchanged(hass: HomeAssistant) -> None:
    await _store(
        hass, 2026, [FIRST, _session("s2", SECOND.plug_start, SECOND.plug_end, card_uid=None)]
    )

    with pytest.raises(session_manager.SessionMergeError) as raised:
        await session_manager.async_merge_sessions(hass, ["s1", "s2"], {})

    assert raised.value.check.violations == ("card_differs",)
    assert await _stored_ids(hass) == ["s1", "s2"]


async def test_a_merge_across_the_turn_of_the_year_is_rejected(hass: HomeAssistant) -> None:
    old = _session("old", "2025-12-31T23:00:00+01:00", "2025-12-31T23:50:00+01:00")
    new = _session("new", "2026-01-01T00:10:00+01:00", "2026-01-01T00:50:00+01:00")
    await _store(hass, 2025, [old])
    await _store(hass, 2026, [new])

    with pytest.raises(session_manager.SessionMergeError) as raised:
        await session_manager.async_merge_sessions(hass, ["old", "new"], {})

    assert raised.value.check.violations == ("year_differs",)
    assert await _stored_ids(hass, 2025) == ["old"]
    assert await _stored_ids(hass, 2026) == ["new"]


async def test_an_unknown_session_is_reported(hass: HomeAssistant) -> None:
    await _store(hass, 2026, [FIRST])

    with pytest.raises(session_manager.SessionNotFoundError):
        await session_manager.async_merge_sessions(hass, ["s1", "missing"], {})


async def test_a_failing_write_leaves_the_sources(hass: HomeAssistant) -> None:
    """an error while writing leaves the original sessions stored."""
    await _store(hass, 2026, [FIRST, SECOND])

    with (
        patch(
            "homeassistant.helpers.storage.Store.async_save",
            side_effect=OSError("disk full"),
        ),
        pytest.raises(OSError),
    ):
        await session_manager.async_merge_sessions(hass, ["s1", "s2"], {})

    assert await _stored_ids(hass) == ["s1", "s2"]


async def test_a_source_changed_meanwhile_is_merged_from_its_current_state(
    hass: HomeAssistant,
) -> None:
    """The merge is formed from the stored list read under the lock."""
    await _store(hass, 2026, [FIRST, SECOND])
    original = SessionYearStore.async_update

    async def _update_then_merge(self: SessionYearStore, update: Any) -> None:
        if not getattr(self, "_changed", False):
            self._changed = True  # type: ignore[attr-defined]
            await original(
                self,
                lambda current: [
                    Session.from_dict({**s.to_dict(), "cost": 2.0}) if s.id == "s2" else s
                    for s in current
                ],
            )
        await original(self, update)

    with patch.object(SessionYearStore, "async_update", _update_then_merge):
        merged = await session_manager.async_merge_sessions(hass, ["s1", "s2"], {})

    assert merged.cost == 2.5


# -------------------------------------------------------------------- service


async def _user(hass: HomeAssistant, *, is_admin: bool) -> MockUser:
    return MockUser(is_owner=is_admin).add_to_hass(hass)


async def test_service_rejects_a_non_admin_user(hass: HomeAssistant) -> None:
    """merge_sessions checks call.context.user_id."""
    await _setup_hub(hass)
    user = await _user(hass, is_admin=False)
    await _store(hass, 2026, [FIRST, SECOND])

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MERGE_SESSIONS,
            {ATTR_SESSION_IDS: ["s1", "s2"], ATTR_CONFIRM: True},
            blocking=True,
            context=Context(user_id=user.id),
        )
    assert await _stored_ids(hass) == ["s1", "s2"]


async def test_service_rejects_a_call_without_confirmation(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _user(hass, is_admin=True)
    await _store(hass, 2026, [FIRST, SECOND])

    with pytest.raises(ServiceValidationError) as raised:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MERGE_SESSIONS,
            {ATTR_SESSION_IDS: ["s1", "s2"], ATTR_CONFIRM: False},
            blocking=True,
            context=Context(user_id=user.id),
        )
    assert raised.value.translation_key == "merge_confirm_required"
    assert await _stored_ids(hass) == ["s1", "s2"]


async def test_service_merges_for_an_admin(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _user(hass, is_admin=True)
    second = _session("s2", SECOND.plug_start, SECOND.plug_end, odometer_km=None)
    await _store(hass, 2026, [FIRST, second])

    await hass.services.async_call(
        DOMAIN,
        SERVICE_MERGE_SESSIONS,
        {ATTR_SESSION_IDS: ["s1", "s2"], ATTR_CONFIRM: True, ATTR_ODOMETER_KM: {"s2": 7700}},
        blocking=True,
        context=Context(user_id=user.id),
    )

    (merged,) = await SessionYearStore(hass, 2026).async_load()
    assert merged.id == "s1"
    assert merged.energy_kwh == 10.0


@pytest.mark.parametrize(
    ("second", "key"),
    [
        (
            _session("s2", SECOND.plug_start, SECOND.plug_end, odometer_km=7701.0),
            "odometer_deviation",
        ),
        (_session("s2", SECOND.plug_start, SECOND.plug_end, odometer_km=None), "odometer_missing"),
        (
            _session("s2", SECOND.plug_start, SECOND.plug_end, card_uid="SYNTHETIC02"),
            "card_differs",
        ),
    ],
)
async def test_service_rejects_an_unmet_condition(
    hass: HomeAssistant, second: Session, key: str
) -> None:
    await _setup_hub(hass)
    user = await _user(hass, is_admin=True)
    await _store(hass, 2026, [FIRST, second])

    with pytest.raises(ServiceValidationError) as raised:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MERGE_SESSIONS,
            {ATTR_SESSION_IDS: ["s1", "s2"], ATTR_CONFIRM: True},
            blocking=True,
            context=Context(user_id=user.id),
        )
    assert raised.value.translation_key == f"merge_{key}"
    assert await _stored_ids(hass) == ["s1", "s2"]


# -------------------------------------------------------------------- websocket


async def _call(client: Any, **params: Any) -> dict[str, Any]:
    await client.send_json_auto_id({"type": "ev_charging/sessions/merge", **params})
    return await client.receive_json()


async def test_command_dry_run_returns_the_preview(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    websocket.async_setup_websocket(hass)
    await _store(hass, 2026, [FIRST, SECOND])
    client = await hass_ws_client(hass)

    response = await _call(client, session_ids=["s1", "s2"], dry_run=True)

    assert response["success"], response
    assert response["result"]["violations"] == []
    assert response["result"]["session"]["energy_kwh"] == 10.0
    assert await _stored_ids(hass) == ["s1", "s2"]


async def test_command_dry_run_names_the_unmet_conditions(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    websocket.async_setup_websocket(hass)
    second = _session("s2", SECOND.plug_start, SECOND.plug_end, odometer_km=None, charge_type="dc")
    await _store(hass, 2026, [FIRST, second])
    client = await hass_ws_client(hass)

    response = await _call(client, session_ids=["s1", "s2"], dry_run=True)

    assert response["success"], response
    assert response["result"]["session"] is None
    assert response["result"]["violations"] == ["odometer_missing", "charge_type_differs"]
    assert response["result"]["missing_odometer"] == ["s2"]


async def test_command_merges_for_an_admin(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    websocket.async_setup_websocket(hass)
    second = _session("s2", SECOND.plug_start, SECOND.plug_end, odometer_km=None)
    await _store(hass, 2026, [FIRST, second, OTHER])
    client = await hass_ws_client(hass)

    response = await _call(client, session_ids=["s1", "s2"], odometer_km={"s2": 7699.5})

    assert response["success"], response
    assert response["result"]["session"]["id"] == "s1"
    assert await _stored_ids(hass) == ["s1", "s3"]


async def test_command_rejects_an_unmet_condition(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    websocket.async_setup_websocket(hass)
    await _store(
        hass, 2026, [FIRST, _session("s2", SECOND.plug_start, SECOND.plug_end, odometer_km=7701.0)]
    )
    client = await hass_ws_client(hass)

    response = await _call(client, session_ids=["s1", "s2"])

    assert not response["success"]
    assert response["error"]["code"] == websocket_api.ERR_INVALID_FORMAT
    assert await _stored_ids(hass) == ["s1", "s2"]


async def test_command_rejects_a_non_administrator(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
) -> None:
    """sessions/merge carries require_admin, also for a dry run."""
    websocket.async_setup_websocket(hass)
    await _store(hass, 2026, [FIRST, SECOND])
    client = await hass_ws_client(hass, hass_read_only_access_token)

    for dry_run in (False, True):
        response = await _call(client, session_ids=["s1", "s2"], dry_run=dry_run)
        assert not response["success"]
        assert response["error"]["code"] == websocket_api.ERR_UNAUTHORIZED
    assert await _stored_ids(hass) == ["s1", "s2"]
