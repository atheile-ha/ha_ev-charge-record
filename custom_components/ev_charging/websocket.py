"""Read-only WebSocket commands that feed the panel and the dashboard cards."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_RECENT_LIMIT,
    DOMAIN,
    LOCATION_EXTERNAL,
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
    """Register the read-only commands. Registering twice is harmless."""
    websocket_api.async_register_command(hass, ws_sessions_list)
    websocket_api.async_register_command(hass, ws_sessions_stats)
    websocket_api.async_register_command(hass, ws_sessions_open)
    websocket_api.async_register_command(hass, ws_vehicles_list)
    websocket_api.async_register_command(hass, ws_live_subscribe)


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
        connection.send_message(websocket_api.event_message(msg["id"], manager.live_payload()))

    connection.subscriptions[msg["id"]] = manager.async_add_live_listener(_push)
    connection.send_result(msg["id"])
    _push()
