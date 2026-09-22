"""Tests for the delete_all_data and retry_address services (I6, 13.3, 7.7)."""

from __future__ import annotations

import os
from typing import Any

import pytest
from custom_components.ev_charging import services
from custom_components.ev_charging.const import (
    ATTR_CONFIRM,
    ATTR_SESSION_ID,
    DOMAIN,
    SERVICE_DELETE_ALL_DATA,
    SERVICE_RETRY_ADDRESS,
    TITLE,
    store_key_sessions,
)
from custom_components.ev_charging.models import HubSettings, Session
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
