"""Tests for the delete_all_data service (I6, 13.3)."""

from __future__ import annotations

import os

import pytest
from custom_components.ev_charging import services
from custom_components.ev_charging.const import (
    ATTR_CONFIRM,
    DOMAIN,
    SERVICE_DELETE_ALL_DATA,
    store_key_sessions,
)
from custom_components.ev_charging.models import Session
from custom_components.ev_charging.store import SessionYearStore
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from pytest_homeassistant_custom_component.common import MockUser


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
