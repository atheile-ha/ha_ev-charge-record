"""WebSocket commands that feed the panel and the dashboard cards."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from . import session_manager
from .const import (
    CURRENT_TYPES,
    DEFAULT_RECENT_LIMIT,
    DOMAIN,
    LOCATION_EXTERNAL,
    LOCATIONS,
    MAX_LIST_LIMIT,
    SESSION_STATUS_FOLLOWUP_OPEN,
    SUBENTRY_TYPE_VEHICLE,
    WS_LIVE_SUBSCRIBE,
)
from .models import Session, Vehicle
from .session_manager import SessionManager
from .store import SessionYearStore, async_list_session_years

_YEAR = vol.All(int, vol.Range(min=1000, max=9999))
_MONTH = vol.All(int, vol.Range(min=1, max=12))


def local_plug_start(session: Session) -> datetime:
    """Return the session's plug_start in local time.

    A session belongs to the year and month of its plug_start in local
    time, never to the month in which it ends or the UTC month.
    """
    parsed = dt_util.parse_datetime(session.plug_start)
    if parsed is None:
        raise ValueError(f"Session {session.id} has an unreadable plug_start")
    return dt_util.as_local(parsed)


def _newest_first(sessions: list[Session]) -> list[Session]:
    """Return the sessions ordered by plug_start, newest first."""
    return sorted(sessions, key=local_plug_start, reverse=True)


def _has_open_followup(session: Session) -> bool:
    """Whether the session still waits for values to be filled in."""
    return session.status == SESSION_STATUS_FOLLOWUP_OPEN or bool(session.open_fields)


def _payload(session: Session) -> dict[str, Any]:
    """Serialize a session for the frontend, with the derived estimate flag."""
    return {**session.to_dict(), "energy_is_estimate": session.energy_is_estimate}


def _sum(values: list[float | None]) -> float:
    """Sum the present values; a session without a value adds nothing."""
    return round(sum(value for value in values if value is not None), 4)


def summarize(sessions: list[Session]) -> dict[str, Any]:
    """Return the sums shown in the overview, counting every session."""
    return {
        "count": len(sessions),
        "energy_kwh": _sum([session.energy_kwh for session in sessions]),
        "energy_is_estimate": any(session.energy_is_estimate for session in sessions),
        "cost": _sum([session.cost for session in sessions]),
        "charge_duration_min": _sum([session.charge_duration_min for session in sessions]),
        "open_followups": sum(1 for session in sessions if _has_open_followup(session)),
    }


def summarize_year(sessions: list[Session]) -> dict[str, Any]:
    """Return the sums of a year, in total and split into internal and external charging.

    Internal is every session at home, with or without the wallbox.
    """
    external = [s for s in sessions if s.location == LOCATION_EXTERNAL]
    internal = [s for s in sessions if s.location != LOCATION_EXTERNAL]
    return {
        "all": summarize(sessions),
        "internal": summarize(internal),
        "external": summarize(external),
    }


@callback
def async_setup_websocket(hass: HomeAssistant) -> None:
    """Register the commands. Registering twice is harmless."""
    websocket_api.async_register_command(hass, ws_sessions_list)
    websocket_api.async_register_command(hass, ws_sessions_stats)
    websocket_api.async_register_command(hass, ws_sessions_open)
    websocket_api.async_register_command(hass, ws_vehicles_list)
    websocket_api.async_register_command(hass, ws_live_subscribe)
    websocket_api.async_register_command(hass, ws_sessions_update)
    websocket_api.async_register_command(hass, ws_sessions_delete)
    websocket_api.async_register_command(hass, ws_sessions_close_followup)
    websocket_api.async_register_command(hass, ws_sessions_correct_vehicle)
    websocket_api.async_register_command(hass, ws_sessions_create)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "ev_charging/sessions/list",
        vol.Optional("year"): _YEAR,
        vol.Optional("month"): _MONTH,
        vol.Optional("limit"): vol.All(int, vol.Range(min=1, max=MAX_LIST_LIMIT)),
    }
)
@websocket_api.async_response
async def ws_sessions_list(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return sessions, newest first, and the years that hold data.

    With a year, all sessions of that year, narrowed to one month if given.
    Without a year, the newest sessions across all years.
    """
    year = msg.get("year")
    month = msg.get("month")
    limit = msg.get("limit")

    if month is not None and year is None:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "month requires year")
        return

    years = await async_list_session_years(hass)
    if year is not None:
        sessions = await SessionYearStore(hass, year).async_load()
        if month is not None:
            sessions = [s for s in sessions if local_plug_start(s).month == month]
        sessions = _newest_first(sessions)
        if limit is not None:
            sessions = sessions[:limit]
    else:
        limit = limit or DEFAULT_RECENT_LIMIT
        sessions = []
        for available_year in reversed(years):
            sessions.extend(
                _newest_first(await SessionYearStore(hass, available_year).async_load())
            )
            if len(sessions) >= limit:
                break
        sessions = sessions[:limit]

    connection.send_result(msg["id"], {"sessions": [_payload(s) for s in sessions], "years": years})


@websocket_api.websocket_command(
    {vol.Required("type"): "ev_charging/sessions/stats", vol.Required("year"): _YEAR}
)
@websocket_api.async_response
async def ws_sessions_stats(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the sums of a year, per month and as a whole, and the years that hold data."""
    year = msg["year"]
    sessions = await SessionYearStore(hass, year).async_load()
    by_month: defaultdict[int, list[Session]] = defaultdict(list)
    for session in sessions:
        by_month[local_plug_start(session).month].append(session)

    connection.send_result(
        msg["id"],
        {
            "year": year,
            "years": await async_list_session_years(hass),
            "year_summary": summarize_year(sessions),
            "months": [
                {"month": month, **summarize(by_month.get(month, []))} for month in range(1, 13)
            ],
        },
    )


@websocket_api.websocket_command({vol.Required("type"): "ev_charging/sessions/open"})
@websocket_api.async_response
async def ws_sessions_open(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the sessions that still wait for values, across all years."""
    open_sessions: list[Session] = []
    for year in await async_list_session_years(hass):
        open_sessions.extend(
            session
            for session in await SessionYearStore(hass, year).async_load()
            if _has_open_followup(session)
        )

    connection.send_result(
        msg["id"], {"sessions": [_payload(s) for s in _newest_first(open_sessions)]}
    )


@websocket_api.websocket_command({vol.Required("type"): "ev_charging/vehicles/list"})
@callback
def ws_vehicles_list(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the configured vehicles and their cards, without the VIN."""
    vehicles = [
        Vehicle.from_dict(subentry.data)
        for entry in hass.config_entries.async_entries(DOMAIN)
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_VEHICLE
    ]
    connection.send_result(
        msg["id"],
        {
            "vehicles": [
                {
                    "id": vehicle.id,
                    "name": vehicle.name,
                    "active": vehicle.active,
                    "is_guest": vehicle.is_guest,
                    "manufacturer": vehicle.manufacturer,
                    "model": vehicle.model,
                    "cards": [
                        {
                            "uid": card.uid,
                            "label": card.label,
                            "type": card.type,
                            "active": card.active,
                        }
                        for card in vehicle.cards
                    ],
                }
                for vehicle in sorted(vehicles, key=lambda vehicle: vehicle.id)
            ]
        },
    )


def _manager(hass: HomeAssistant) -> SessionManager | None:
    """Return the session manager of the loaded entry, if a wallbox is configured."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data.manager
    return None


@websocket_api.websocket_command({vol.Required("type"): WS_LIVE_SUBSCRIBE})
@callback
def ws_live_subscribe(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send the live values of the running session now and after every change.

    Reading needs a signed-in user only. The values are resolved on the
    server from the mapped source entities, so the card is not tied to the
    publish interval of the entities.
    """
    manager = _manager(hass)
    if manager is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "No wallbox is configured")
        return

    @callback
    def _push() -> None:
        connection.send_message(websocket_api.event_message(msg["id"], manager.live_blocks()))

    connection.subscriptions[msg["id"]] = manager.async_add_live_listener(_push)
    connection.send_result(msg["id"])
    _push()


# --------------------------------------------------------------------- write commands (I7)


def _ws_offset_datetime(value: Any) -> datetime:
    """Validate an ISO 8601 timestamp with a UTC offset (6.4)."""
    if not isinstance(value, str):
        raise vol.Invalid("expected a string")
    try:
        return session_manager.parse_offset_datetime(value)
    except ValueError as err:
        raise vol.Invalid(str(err)) from err


_PERCENT = vol.All(vol.Coerce(float), vol.Range(min=0, max=100))
_NON_NEGATIVE = vol.All(vol.Coerce(float), vol.Range(min=0))


def _send_operation_error(
    connection: websocket_api.ActiveConnection,
    msg_id: int,
    err: session_manager.SessionOperationError,
) -> None:
    """Translate a rejected session correction into a WebSocket error response."""
    code = (
        websocket_api.ERR_NOT_FOUND
        if isinstance(err, session_manager.SessionNotFoundError)
        else websocket_api.ERR_INVALID_FORMAT
    )
    connection.send_error(msg_id, code, str(err))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "ev_charging/sessions/update",
        vol.Required("session_id"): str,
        vol.Optional("soc_start"): _PERCENT,
        vol.Optional("soc_end"): _PERCENT,
        vol.Optional("odometer_km"): _NON_NEGATIVE,
        vol.Optional("energy_billed_kwh"): _NON_NEGATIVE,
        vol.Optional("cost"): _NON_NEGATIVE,
        vol.Optional("charge_type"): vol.In(CURRENT_TYPES),
        vol.Optional("address"): str,
        vol.Optional("note"): str,
        vol.Optional("provider"): str,
        vol.Optional("plug_end"): _ws_offset_datetime,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_sessions_update(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Apply a nacherfassung or correction to a stored session (10, 13, 15)."""
    values = {key: value for key, value in msg.items() if key not in ("type", "id", "session_id")}
    try:
        updated = await session_manager.async_update_session(hass, msg["session_id"], values)
    except session_manager.SessionOperationError as err:
        _send_operation_error(connection, msg["id"], err)
        return
    connection.send_result(msg["id"], {"session": _payload(updated)})


@websocket_api.websocket_command(
    {vol.Required("type"): "ev_charging/sessions/delete", vol.Required("session_id"): str}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_sessions_delete(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Remove one stored session (13)."""
    try:
        await session_manager.async_delete_session(hass, msg["session_id"])
    except session_manager.SessionOperationError as err:
        _send_operation_error(connection, msg["id"], err)
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {vol.Required("type"): "ev_charging/sessions/close_followup", vol.Required("session_id"): str}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_sessions_close_followup(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Accept a session's missing values as final (10)."""
    try:
        updated = await session_manager.async_close_followup(hass, msg["session_id"])
    except session_manager.SessionOperationError as err:
        _send_operation_error(connection, msg["id"], err)
        return
    connection.send_result(msg["id"], {"session": _payload(updated)})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "ev_charging/sessions/correct_vehicle",
        vol.Required("session_id"): str,
        vol.Required("vehicle_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_sessions_correct_vehicle(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Reassign a stored session to a different vehicle, or resolve an unresolved one (7.8)."""
    try:
        updated = await session_manager.async_correct_vehicle(
            hass, msg["session_id"], msg["vehicle_id"]
        )
    except session_manager.SessionOperationError as err:
        _send_operation_error(connection, msg["id"], err)
        return
    connection.send_result(msg["id"], {"session": _payload(updated)})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "ev_charging/sessions/create",
        vol.Required("location"): vol.In(LOCATIONS),
        vol.Required("plug_start"): _ws_offset_datetime,
        vol.Required("plug_end"): _ws_offset_datetime,
        vol.Optional("vehicle_id"): str,
        vol.Optional("soc_start"): _PERCENT,
        vol.Optional("soc_end"): _PERCENT,
        vol.Optional("odometer_km"): _NON_NEGATIVE,
        vol.Optional("energy_billed_kwh"): _NON_NEGATIVE,
        vol.Optional("charge_type"): vol.In(CURRENT_TYPES),
        vol.Optional("cost"): _NON_NEGATIVE,
        vol.Optional("address"): str,
        vol.Optional("note"): str,
        vol.Optional("provider"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_sessions_create(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Fully reconstruct a past charging session by hand (13)."""
    fields = {key: value for key, value in msg.items() if key not in ("type", "id")}
    try:
        created = await session_manager.async_create_session(hass, fields)
    except session_manager.SessionOperationError as err:
        _send_operation_error(connection, msg["id"], err)
        return
    connection.send_result(msg["id"], {"session": _payload(created)})
