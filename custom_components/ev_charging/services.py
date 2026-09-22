"""Service handlers with permission checks (13.3, I6)."""

from __future__ import annotations

import logging
from dataclasses import replace

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from . import geocoding
from .const import (
    ATTR_CONFIRM,
    ATTR_SESSION_ID,
    DOMAIN,
    SERVICE_DELETE_ALL_DATA,
    SERVICE_RETRY_ADDRESS,
)
from .models import HubSettings, Session
from .store import SessionYearStore, async_list_session_years

_LOGGER = logging.getLogger(__name__)

_DELETE_ALL_DATA_SCHEMA = vol.Schema({vol.Required(ATTR_CONFIRM): cv.boolean})
_RETRY_ADDRESS_SCHEMA = vol.Schema({vol.Required(ATTR_SESSION_ID): cv.string})


def _now_iso() -> str:
    """Format the current moment as local ISO 8601 with offset, to the second."""
    return dt_util.now().replace(microsecond=0).isoformat()


async def _async_require_admin(hass: HomeAssistant, call: ServiceCall, *, permission: str) -> None:
    """Reject a service call unless it comes from an administrator (I6)."""
    user_id = call.context.user_id
    user = await hass.auth.async_get_user(user_id) if user_id else None
    if user is None or not user.is_admin:
        raise Unauthorized(context=call.context, permission=permission)


async def _async_handle_delete_all_data(hass: HomeAssistant, call: ServiceCall) -> None:
    """Delete every session of every year, after confirmation and admin check."""
    await _async_require_admin(hass, call, permission=SERVICE_DELETE_ALL_DATA)
    if not call.data.get(ATTR_CONFIRM):
        raise ServiceValidationError("delete_all_data requires confirm: true")

    years = await async_list_session_years(hass)
    for year in years:
        await SessionYearStore(hass, year).async_save([])
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED and entry.runtime_data.manager is not None:
            await entry.runtime_data.manager.async_refresh_followups()
    _LOGGER.info("Deleted all ev_charging session data for years: %s", years)


def _hub_settings(hass: HomeAssistant) -> HubSettings | None:
    """Return the global settings of the loaded hub entry, if there is one."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return HubSettings.from_dict(entry.data)
    return None


async def _async_handle_retry_address(hass: HomeAssistant, call: ServiceCall) -> None:
    """Look up the address of one stored session again, after admin check (7.7)."""
    await _async_require_admin(hass, call, permission=SERVICE_RETRY_ADDRESS)
    session_id = call.data[ATTR_SESSION_ID]

    settings = _hub_settings(hass)
    if settings is None or not settings.geocoding_enabled or not settings.geocoding_contact:
        raise ServiceValidationError("Geocoding is disabled")

    for year in await async_list_session_years(hass):
        store = SessionYearStore(hass, year)
        sessions = await store.async_load()
        target = next((session for session in sessions if session.id == session_id), None)
        if target is None:
            continue
        if target.latitude is None or target.longitude is None:
            raise ServiceValidationError(f"Session {session_id} has no coordinates to look up")

        address = await geocoding.async_get_queue(hass).async_lookup(
            hass,
            url=settings.geocoding_url,
            contact=settings.geocoding_contact,
            latitude=target.latitude,
            longitude=target.longitude,
        )
        if address is None:
            return

        def _apply(current: list[Session], address: str = address) -> list[Session]:
            return [
                replace(
                    session, address=address, address_retry_pending=False, modified_at=_now_iso()
                )
                if session.id == session_id
                else session
                for session in current
            ]

        await store.async_update(_apply)
        return

    raise ServiceValidationError(f"No session with id {session_id}")


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the domain's services, once per Home Assistant run."""
    if hass.services.has_service(DOMAIN, SERVICE_DELETE_ALL_DATA):
        return

    async def _delete_all_data(call: ServiceCall) -> None:
        await _async_handle_delete_all_data(hass, call)

    async def _retry_address(call: ServiceCall) -> None:
        await _async_handle_retry_address(hass, call)

    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_ALL_DATA, _delete_all_data, schema=_DELETE_ALL_DATA_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RETRY_ADDRESS, _retry_address, schema=_RETRY_ADDRESS_SCHEMA
    )


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Remove the domain's services."""
    hass.services.async_remove(DOMAIN, SERVICE_DELETE_ALL_DATA)
    hass.services.async_remove(DOMAIN, SERVICE_RETRY_ADDRESS)
