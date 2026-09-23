"""Tests for the delete_all_data and retry_address services (I6, 13.3, 7.7)."""

from __future__ import annotations

import os
from typing import Any

import pytest
from custom_components.ev_charging import services
from custom_components.ev_charging.const import (
    ATTR_CONFIRM,
    ATTR_SESSION_ID,
    ATTR_VEHICLE_ID,
    DOMAIN,
    SERVICE_CLOSE_FOLLOWUP,
    SERVICE_CORRECT_VEHICLE,
    SERVICE_CREATE_SESSION,
    SERVICE_DELETE_ALL_DATA,
    SERVICE_DELETE_SESSION,
    SERVICE_RETRY_ADDRESS,
    SERVICE_UPDATE_SESSION,
    SUBENTRY_TYPE_VEHICLE,
    TITLE,
    store_key_sessions,
)
from custom_components.ev_charging.models import HubSettings, Session, Vehicle
from custom_components.ev_charging.store import SessionYearStore
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Give this module's hass a private config dir instead of the shared default.

    _touch_year_files below writes real files directly; the plugin's default
    config dir is a fixed path shared by every test in the run, so real
    files written there would leak between tests.
    """
    return hass_tmp_config_dir


def _touch_year_files(storage_dir: str, years: list[int]) -> None:
    """Create the real files async_list_session_years scans for.

    Store I/O is mocked to an in-memory dict under the test harness and
    never reaches real disk, so the directory scan needs real files placed
    directly, alongside the actual (mocked) session content below.
    """
    os.makedirs(storage_dir, exist_ok=True)
    for year in years:
        open(os.path.join(storage_dir, store_key_sessions(year)), "w", encoding="utf-8").close()


async def _add_user(hass: HomeAssistant, *, is_admin: bool) -> MockUser:
    return MockUser(is_owner=is_admin).add_to_hass(hass)


async def _setup_hub(hass: HomeAssistant, **overrides: Any) -> MockConfigEntry:
    """Set up a bare hub entry, no wallbox or vehicle, with geocoding enabled by default."""
    settings: dict[str, Any] = {
        "geocoding_enabled": True,
        "geocoding_contact": "test@example.invalid",
    }
    settings.update(overrides)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data=HubSettings(**settings).to_dict(),
        version=5,
        minor_version=1,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_delete_all_data_rejects_non_admin_user(hass: HomeAssistant) -> None:
    """A non-administrator's call is rejected before anything is confirmed or deleted."""
    services.async_setup_services(hass)
    user = await _add_user(hass, is_admin=False)
    await SessionYearStore(hass, 2026).async_save(
        [
            Session(
                id="a",
                location="home",
                plug_start="2026-01-01T00:00:00+01:00",
                identification_source="unresolved",
            )
        ]
    )

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DELETE_ALL_DATA,
            {ATTR_CONFIRM: True},
            blocking=True,
            context=Context(user_id=user.id),
        )

    assert len(await SessionYearStore(hass, 2026).async_load()) == 1


async def test_delete_all_data_rejects_missing_confirmation(hass: HomeAssistant) -> None:
    """An admin call without confirm: true is rejected."""
    services.async_setup_services(hass)
    user = await _add_user(hass, is_admin=True)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DELETE_ALL_DATA,
            {ATTR_CONFIRM: False},
            blocking=True,
            context=Context(user_id=user.id),
        )


async def test_delete_all_data_clears_every_year_for_admin_with_confirmation(
    hass: HomeAssistant,
) -> None:
    """A confirmed admin call empties every existing year's session store."""
    services.async_setup_services(hass)
    user = await _add_user(hass, is_admin=True)
    session = Session(
        id="a",
        location="home",
        plug_start="2026-01-01T00:00:00+01:00",
        identification_source="unresolved",
    )
    await SessionYearStore(hass, 2025).async_save([session])
    await SessionYearStore(hass, 2026).async_save([session])
    await hass.async_add_executor_job(_touch_year_files, hass.config.path(".storage"), [2025, 2026])

    await hass.services.async_call(
        DOMAIN,
        SERVICE_DELETE_ALL_DATA,
        {ATTR_CONFIRM: True},
        blocking=True,
        context=Context(user_id=user.id),
    )

    assert await SessionYearStore(hass, 2025).async_load() == []
    assert await SessionYearStore(hass, 2026).async_load() == []


def _external_session(**overrides: Any) -> Session:
    fields: dict[str, Any] = {
        "id": "2026-06-01T10:00:00_v001",
        "location": "external",
        "plug_start": "2026-06-01T10:00:00+02:00",
        "identification_source": "vehicle_api",
        "latitude": 48.1,
        "longitude": 11.6,
        "address_retry_pending": True,
    }
    fields.update(overrides)
    return Session(**fields)


async def test_retry_address_rejects_non_admin_user(hass: HomeAssistant) -> None:
    """A non-administrator's call is rejected."""
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=False)
    await SessionYearStore(hass, 2026).async_save([_external_session()])

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RETRY_ADDRESS,
            {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001"},
            blocking=True,
            context=Context(user_id=user.id),
        )


async def test_retry_address_rejects_when_geocoding_is_disabled(hass: HomeAssistant) -> None:
    """Geocoding disabled by the user is never bypassed by a manual retry."""
    await _setup_hub(hass, geocoding_enabled=False)
    user = await _add_user(hass, is_admin=True)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RETRY_ADDRESS,
            {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001"},
            blocking=True,
            context=Context(user_id=user.id),
        )


async def test_retry_address_rejects_unknown_session(hass: HomeAssistant) -> None:
    """A session id that does not exist in any year is rejected."""
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=True)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RETRY_ADDRESS,
            {ATTR_SESSION_ID: "does-not-exist"},
            blocking=True,
            context=Context(user_id=user.id),
        )


async def test_retry_address_rejects_a_session_without_coordinates(hass: HomeAssistant) -> None:
    """A session that never captured coordinates cannot be looked up."""
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=True)
    await SessionYearStore(hass, 2026).async_save(
        [_external_session(latitude=None, longitude=None)]
    )
    await hass.async_add_executor_job(_touch_year_files, hass.config.path(".storage"), [2026])

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RETRY_ADDRESS,
            {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001"},
            blocking=True,
            context=Context(user_id=user.id),
        )


async def test_retry_address_updates_the_stored_session(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A successful lookup writes the address and clears the pending flag."""
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=True)
    await SessionYearStore(hass, 2026).async_save([_external_session()])
    await hass.async_add_executor_job(_touch_year_files, hass.config.path(".storage"), [2026])
    aioclient_mock.get(
        "https://nominatim.openstreetmap.org/reverse", json={"display_name": "Marienplatz, München"}
    )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RETRY_ADDRESS,
        {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001"},
        blocking=True,
        context=Context(user_id=user.id),
    )

    (updated,) = await SessionYearStore(hass, 2026).async_load()
    assert updated.address == "Marienplatz, München"
    assert updated.address_retry_pending is False


async def test_retry_address_leaves_the_session_unchanged_on_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A failed lookup keeps the session pending instead of writing a wrong or empty address."""
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=True)
    await SessionYearStore(hass, 2026).async_save([_external_session()])
    await hass.async_add_executor_job(_touch_year_files, hass.config.path(".storage"), [2026])
    aioclient_mock.get("https://nominatim.openstreetmap.org/reverse", status=503)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RETRY_ADDRESS,
        {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001"},
        blocking=True,
        context=Context(user_id=user.id),
    )

    (unchanged,) = await SessionYearStore(hass, 2026).async_load()
    assert unchanged.address is None
    assert unchanged.address_retry_pending is True


# ------------------------------------------------------------------------- I6


def _home_session(**overrides: Any) -> Session:
    fields: dict[str, Any] = {
        "id": "2026-06-01T10:00:00_v001",
        "location": "home",
        "plug_start": "2026-06-01T10:00:00+02:00",
        "identification_source": "manual",
    }
    fields.update(overrides)
    return Session(**fields)


async def _store_session(hass: HomeAssistant, session: Session, year: int = 2026) -> None:
    await SessionYearStore(hass, year).async_save([session])
    await hass.async_add_executor_job(_touch_year_files, hass.config.path(".storage"), [year])


async def test_update_session_rejects_non_admin_user(hass: HomeAssistant) -> None:
    """I6: update_session checks call.context.user_id like every writing service."""
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=False)
    await _store_session(hass, _home_session(open_fields=("odometer_km",)))

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPDATE_SESSION,
            {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001", "odometer_km": 7000, "note": "checked"},
            blocking=True,
            context=Context(user_id=user.id),
        )
    (unchanged,) = await SessionYearStore(hass, 2026).async_load()
    assert unchanged.note is None
    assert unchanged.odometer_km is None


async def test_update_session_fills_a_field_for_an_admin(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=True)
    await _store_session(hass, _home_session(open_fields=("odometer_km",)))

    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_SESSION,
        {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001", "odometer_km": 7000, "note": "checked"},
        blocking=True,
        context=Context(user_id=user.id),
    )

    (updated,) = await SessionYearStore(hass, 2026).async_load()
    assert updated.note == "checked"
    assert updated.odometer_km == 7000
    assert updated.open_fields == ()


async def test_delete_session_rejects_non_admin_user(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=False)
    await _store_session(hass, _home_session())

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DELETE_SESSION,
            {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001"},
            blocking=True,
            context=Context(user_id=user.id),
        )
    assert len(await SessionYearStore(hass, 2026).async_load()) == 1


async def test_delete_session_removes_it_for_an_admin(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=True)
    await _store_session(hass, _home_session())

    await hass.services.async_call(
        DOMAIN,
        SERVICE_DELETE_SESSION,
        {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001"},
        blocking=True,
        context=Context(user_id=user.id),
    )

    assert await SessionYearStore(hass, 2026).async_load() == []


async def test_close_followup_rejects_non_admin_user(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=False)
    await _store_session(hass, _home_session(status="followup_open", open_fields=("soc_start",)))

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CLOSE_FOLLOWUP,
            {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001"},
            blocking=True,
            context=Context(user_id=user.id),
        )
    (unchanged,) = await SessionYearStore(hass, 2026).async_load()
    assert unchanged.status == "followup_open"


async def test_close_followup_completes_the_session_for_an_admin(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=True)
    await _store_session(hass, _home_session(status="followup_open", open_fields=("soc_start",)))

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOSE_FOLLOWUP,
        {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001"},
        blocking=True,
        context=Context(user_id=user.id),
    )

    (updated,) = await SessionYearStore(hass, 2026).async_load()
    assert updated.status == "complete"
    assert updated.open_fields == ()


def _add_vehicle_subentry(hass: HomeAssistant, vehicle: Vehicle) -> None:
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


async def test_correct_vehicle_rejects_non_admin_user(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    _add_vehicle_subentry(hass, Vehicle(id="v002", name="EQB", capacity_kwh=70.5))
    user = await _add_user(hass, is_admin=False)
    await _store_session(hass, _home_session(vehicle_id="v001"))

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CORRECT_VEHICLE,
            {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001", ATTR_VEHICLE_ID: "v002"},
            blocking=True,
            context=Context(user_id=user.id),
        )
    (unchanged,) = await SessionYearStore(hass, 2026).async_load()
    assert unchanged.vehicle_id == "v001"


async def test_correct_vehicle_reassigns_it_for_an_admin(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    _add_vehicle_subentry(hass, Vehicle(id="v002", name="EQB", capacity_kwh=70.5))
    user = await _add_user(hass, is_admin=True)
    await _store_session(hass, _home_session(vehicle_id="v001", vehicle_name="GLB"))

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CORRECT_VEHICLE,
        {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001", ATTR_VEHICLE_ID: "v002"},
        blocking=True,
        context=Context(user_id=user.id),
    )

    (updated,) = await SessionYearStore(hass, 2026).async_load()
    assert updated.vehicle_id == "v002"
    assert updated.vehicle_name == "EQB"
    assert updated.identification_corrected is True


async def test_correct_vehicle_rejects_an_unknown_vehicle(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=True)
    await _store_session(hass, _home_session())

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CORRECT_VEHICLE,
            {ATTR_SESSION_ID: "2026-06-01T10:00:00_v001", ATTR_VEHICLE_ID: "does-not-exist"},
            blocking=True,
            context=Context(user_id=user.id),
        )


async def test_create_session_rejects_non_admin_user(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=False)

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CREATE_SESSION,
            {
                "location": "external",
                "plug_start": "2026-06-01T10:00:00+02:00",
                "plug_end": "2026-06-01T12:00:00+02:00",
            },
            blocking=True,
            context=Context(user_id=user.id),
        )
    assert await SessionYearStore(hass, 2026).async_load() == []


async def test_create_session_stores_a_new_session_for_an_admin(hass: HomeAssistant) -> None:
    await _setup_hub(hass)
    user = await _add_user(hass, is_admin=True)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CREATE_SESSION,
        {
            "location": "external",
            "plug_start": "2026-06-01T10:00:00+02:00",
            "plug_end": "2026-06-01T12:00:00+02:00",
            "cost": 12.5,
        },
        blocking=True,
        context=Context(user_id=user.id),
    )

    (created,) = await SessionYearStore(hass, 2026).async_load()
    assert created.location == "external"
    assert created.cost == 12.5
