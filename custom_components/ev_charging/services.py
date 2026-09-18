"""Service handlers with permission checks (13.3, I6)."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import config_validation as cv

from .const import ATTR_CONFIRM, DOMAIN, SERVICE_DELETE_ALL_DATA
from .store import SessionYearStore, async_list_session_years

_LOGGER = logging.getLogger(__name__)

_DELETE_ALL_DATA_SCHEMA = vol.Schema({vol.Required(ATTR_CONFIRM): cv.boolean})


async def _async_require_admin(hass: HomeAssistant, call: ServiceCall) -> None:
    """Reject a service call unless it comes from an administrator (I6)."""
    user_id = call.context.user_id
    user = await hass.auth.async_get_user(user_id) if user_id else None
    if user is None or not user.is_admin:
        raise Unauthorized(context=call.context, permission="delete_all_data")


async def _async_handle_delete_all_data(hass: HomeAssistant, call: ServiceCall) -> None:
    """Delete every session of every year, after confirmation and admin check."""
    await _async_require_admin(hass, call)
    if not call.data.get(ATTR_CONFIRM):
        raise ServiceValidationError("delete_all_data requires confirm: true")

    years = await async_list_session_years(hass)
    for year in years:
        await SessionYearStore(hass, year).async_save([])
    _LOGGER.info("Deleted all ev_charging session data for years: %s", years)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the domain's services, once per Home Assistant run."""
    if hass.services.has_service(DOMAIN, SERVICE_DELETE_ALL_DATA):
        return

    async def _delete_all_data(call: ServiceCall) -> None:
        await _async_handle_delete_all_data(hass, call)

    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_ALL_DATA, _delete_all_data, schema=_DELETE_ALL_DATA_SCHEMA
    )


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Remove the domain's services."""
    hass.services.async_remove(DOMAIN, SERVICE_DELETE_ALL_DATA)
