"""Notifications: persistent ones on rotating ids, and up to two notification targets."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

import voluptuous as vol
from homeassistant.components import persistent_notification
from homeassistant.const import EVENT_SERVICE_REGISTERED, EVENT_SERVICE_REMOVED
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.translation import async_get_translations
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    LOCATION_EXTERNAL,
    LOCATIONS,
    NOTIFY_DOMAIN,
    NOTIFY_SERVICE_SEND_MESSAGE,
    NOTIFY_TARGET_ENTITY,
    PERSISTENT_NOTIFICATION_ID_PREFIX,
    PERSISTENT_NOTIFICATION_SLOTS,
    SESSION_STATUS_FOLLOWUP_OPEN,
    SESSION_TIMEOUT_H,
)
from .models import HubSettings, NotifyTarget, Session

_LOGGER = logging.getLogger(__name__)

_TEXT_PREFIX = f"component.{DOMAIN}.selector.notification.options."

# Builds title and message from the texts once they are loaded.
type MessageBuilder = Callable[[Texts], tuple[str, str]]


def persistent_notification_id(slot: int) -> str:
    """Return the id of a persistent notification slot, counted from 0."""
    return f"{PERSISTENT_NOTIFICATION_ID_PREFIX}{slot + 1}"


def format_number(value: float, digits: int, separator: str) -> str:
    """Format a number with a fixed count of decimals and the given decimal separator."""
    return f"{value:.{digits}f}".replace(".", separator)


def service_name(target: NotifyTarget) -> str:
    """Return the name of a classic notify service, without its domain."""
    return target.target.removeprefix(f"{NOTIFY_DOMAIN}.")


def target_present(hass: HomeAssistant, target: NotifyTarget) -> bool:
    """Whether a notification target currently exists in Home Assistant."""
    if target.kind == NOTIFY_TARGET_ENTITY:
        return hass.states.get(target.target) is not None
    return hass.services.has_service(NOTIFY_DOMAIN, service_name(target))


class Texts:
    """The notification texts of the configured language, with number and time formatting."""

    def __init__(self, translations: dict[str, str]) -> None:
        """Wrap the loaded translations."""
        self._translations = translations

    def raw(self, key: str) -> str:
        """Return a text as it stands, or its key if it is missing."""
        return self._translations.get(f"{_TEXT_PREFIX}{key}", key)

    def get(self, key: str, **placeholders: Any) -> str:
        """Return a text with its placeholders filled in."""
        text = self.raw(key)
        try:
            return text.format(**placeholders)
        except KeyError, IndexError, ValueError:
            return text

    def number(self, value: float, digits: int) -> str:
        """Format a number in the style of the language."""
        return format_number(value, digits, self.raw("decimal_separator"))

    def moment(self, value: datetime) -> str:
        """Format a moment in local time in the style of the language."""
        return dt_util.as_local(value).strftime(self.raw("datetime_format"))

    def location(self, location: str) -> str:
        """Return the name of a charging location."""
        return self.raw(f"location_{location}") if location in LOCATIONS else location


def _parse(value: str | None) -> datetime | None:
    """Read a stored moment."""
    return dt_util.parse_datetime(value) if value else None


def _vehicle_name(texts: Texts, session: Session) -> str:
    """Return the vehicle a stored session belongs to, or the unassigned text."""
    if session.vehicle_id is None or not session.vehicle_name:
        return texts.raw("unassigned")
    return session.vehicle_name


def _has_open_fields(session: Session) -> bool:
    """Whether a stored session still waits for values."""
    return session.status == SESSION_STATUS_FOLLOWUP_OPEN or bool(session.open_fields)


def summary_lines(texts: Texts, session: Session, currency: str) -> list[str]:
    """Return the summary lines of a finished session, leaving out a line without its values."""
    lines = [
        texts.get(
            "summary_vehicle",
            vehicle=_vehicle_name(texts, session),
            location=texts.location(session.location),
        )
    ]
    if session.soc_start is not None and session.soc_end is not None:
        lines.append(
            texts.get(
                "summary_soc",
                soc_start=texts.number(session.soc_start, 0),
                soc_end=texts.number(session.soc_end, 0),
            )
        )
    if session.energy_kwh is not None:
        lines.append(texts.get("summary_energy", energy=texts.number(session.energy_kwh, 3)))
    if session.energy_grid_kwh is not None and session.energy_solar_kwh is not None:
        lines.append(
            texts.get(
                "summary_split",
                grid=texts.number(session.energy_grid_kwh, 3),
                solar=texts.number(session.energy_solar_kwh, 3),
            )
        )
    if session.cost is not None:
        lines.append(
            texts.get("summary_cost", cost=texts.number(session.cost, 2), currency=currency)
        )
    if session.charge_duration_min is not None:
        lines.append(
            texts.get(
                "summary_duration",
                duration=texts.number(session.charge_duration_min, 0),
                phases=session.phase_count if session.phase_count is not None else 0,
            )
        )
    if _has_open_fields(session):
        lines.append(texts.raw("summary_followup"))
    return lines


class Notifier:
    """Sends the notifications of the session capture.

    Every public method returns at once; sending runs as a task of its own.
    A persistent notification takes the next of the rotating ids when it is
    requested, so the order of the ids follows the order of the occasions.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        settings: HubSettings,
        *,
        next_slot: int,
        on_slot_change: Callable[[int], None],
        on_target_check: Callable[[int, NotifyTarget, bool], None],
    ) -> None:
        """Prepare the notifier.

        next_slot is the persistent notification slot to use next, counted
        from 0. on_slot_change receives the new value whenever a slot was
        taken. on_target_check receives the target number, counted from 1,
        the target and whether it exists, whenever that was looked at.
        """
        self._hass = hass
        self._settings = settings
        self._next_slot = next_slot % PERSISTENT_NOTIFICATION_SLOTS
        self._on_slot_change = on_slot_change
        self._on_target_check = on_target_check
        self._unsubs: list[CALLBACK_TYPE] = []

    @property
    def next_slot(self) -> int:
        """Return the persistent notification slot used next, counted from 0."""
        return self._next_slot

    # ------------------------------------------------------------- targets

    @callback
    def async_start(self) -> None:
        """Watch the configured targets and check them once Home Assistant has started."""
        targets = self._configured_targets()
        if not targets:
            return
        entity_ids = [
            target.target for _number, target in targets if target.kind == NOTIFY_TARGET_ENTITY
        ]
        if entity_ids:
            self._unsubs.append(
                async_track_state_change_event(self._hass, entity_ids, self._on_entity_event)
            )
        if any(target.kind != NOTIFY_TARGET_ENTITY for _number, target in targets):
            for event_type in (EVENT_SERVICE_REGISTERED, EVENT_SERVICE_REMOVED):
                self._unsubs.append(
                    self._hass.bus.async_listen(
                        event_type,
                        self._on_service_event,
                        event_filter=self._is_notify_service_event,
                    )
                )
        self._unsubs.append(async_at_started(self._hass, self._on_started))

    @callback
    def stop(self) -> None:
        """Stop watching the targets."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    def _configured_targets(self) -> list[tuple[int, NotifyTarget]]:
        """Return the configured targets with their number, counted from 1."""
        return [
            (number, target)
            for number, target in enumerate(self._settings.notify_targets, start=1)
            if target is not None
        ]

    @callback
    def _on_started(self, _hass: HomeAssistant) -> None:
        """Check every target once all integrations had the chance to provide theirs."""
        for number, target in self._configured_targets():
            self._on_target_check(number, target, target_present(self._hass, target))

    @callback
    def _on_entity_event(self, event: Event[EventStateChangedData]) -> None:
        """Note a target entity that was removed or came back."""
        entity_id = event.data["entity_id"]
        present = event.data["new_state"] is not None
        for number, target in self._configured_targets():
            if target.kind == NOTIFY_TARGET_ENTITY and target.target == entity_id:
                self._on_target_check(number, target, present)

    @callback
    def _is_notify_service_event(self, event_data: dict[str, Any]) -> bool:
        """Whether a service event concerns the notify domain."""
        return event_data.get("domain") == NOTIFY_DOMAIN

    @callback
    def _on_service_event(self, event: Event[Any]) -> None:
        """Note a target service that was removed or registered."""
        name = event.data.get("service")
        present = event.event_type == EVENT_SERVICE_REGISTERED
        for number, target in self._configured_targets():
            if target.kind != NOTIFY_TARGET_ENTITY and service_name(target) == name:
                self._on_target_check(number, target, present)

    # ------------------------------------------------------------ occasions

    @callback
    def session_ended(self, session: Session) -> None:
        """Report a finished session, and its open values if there are any."""
        settings = self._settings
        external = session.location == LOCATION_EXTERNAL
        currency = self._hass.config.currency

        def _build(texts: Texts) -> tuple[str, str]:
            title = texts.raw("title_external_end" if external else "title_session_end")
            return title, "\n".join(summary_lines(texts, session, currency))

        self._dispatch(
            persistent=settings.persistent_on_session_end,
            targets=settings.notify_on_external_end if external else settings.notify_on_session_end,
            build=_build,
        )
        self._followup(session)

    @callback
    def session_closed_stale(self, session: Session, source_name: str) -> None:
        """Report a session closed because its source gave no usable state for too long."""
        settings = self._settings

        def _build(texts: Texts) -> tuple[str, str]:
            end = _parse(session.plug_end)
            message = texts.get(
                "stale",
                vehicle=_vehicle_name(texts, session),
                source=source_name,
                hours=SESSION_TIMEOUT_H,
                end=texts.moment(end) if end is not None else texts.raw("not_available"),
            )
            return texts.raw("title_stale"), message

        self._dispatch(
            persistent=settings.persistent_on_error, targets=settings.notify_on_error, build=_build
        )
        self._followup(session)

    @callback
    def session_started(
        self,
        vehicle_name: str | None,
        location: str,
        start: datetime,
        soc: float | None,
        odometer_km: float | None,
    ) -> None:
        """Report the beginning of a session at home: the vehicle, its state of charge and odometer.

        vehicle_name is None for a session no vehicle was assigned to.
        """

        def _build(texts: Texts) -> tuple[str, str]:
            lines = [
                texts.get(
                    "session_start",
                    vehicle=vehicle_name or texts.raw("unassigned"),
                    location=texts.location(location),
                    start=texts.moment(start),
                )
            ]
            if soc is not None:
                lines.append(texts.get("external_start_soc", soc=texts.number(soc, 0)))
            if odometer_km is not None:
                lines.append(
                    texts.get("session_start_odometer", odometer=texts.number(odometer_km, 0))
                )
            return texts.raw("title_session_start"), "\n".join(lines)

        self._dispatch(
            persistent=False, targets=self._settings.notify_on_session_start, build=_build
        )

    @callback
    def external_started(self, vehicle_name: str, start: datetime, soc: float | None) -> None:
        """Report the beginning of an external charging session."""

        def _build(texts: Texts) -> tuple[str, str]:
            lines = [texts.get("external_start", vehicle=vehicle_name, start=texts.moment(start))]
            if soc is not None:
                lines.append(texts.get("external_start_soc", soc=texts.number(soc, 0)))
            return texts.raw("title_external_start"), "\n".join(lines)

        self._dispatch(
            persistent=False, targets=self._settings.notify_on_external_start, build=_build
        )

    @callback
    def error_reported(self, source_name: str, error: str, since: datetime) -> None:
        """Report a charging error: which error, from which source, since when."""
        settings = self._settings

        def _build(texts: Texts) -> tuple[str, str]:
            message = texts.get("error", source=source_name, error=error, since=texts.moment(since))
            return texts.raw("title_error"), message

        self._dispatch(
            persistent=settings.persistent_on_error, targets=settings.notify_on_error, build=_build
        )

    def _followup(self, session: Session) -> None:
        """Report a finished session that still waits for values."""
        if not _has_open_fields(session):
            return

        def _build(texts: Texts) -> tuple[str, str]:
            start = _parse(session.plug_start)
            message = texts.get(
                "followup",
                vehicle=_vehicle_name(texts, session),
                location=texts.location(session.location),
                start=texts.moment(start) if start is not None else texts.raw("not_available"),
                count=len(session.open_fields),
            )
            return texts.raw("title_followup"), message

        self._dispatch(persistent=False, targets=self._settings.notify_on_followup, build=_build)

    # -------------------------------------------------------------- sending

    def _dispatch(self, *, persistent: bool, targets: bool, build: MessageBuilder) -> None:
        """Send one notification where its occasion is switched on, without waiting."""
        notification_id = None
        if persistent and self._settings.persistent_enabled:
            notification_id = persistent_notification_id(self._next_slot)
            self._next_slot = (self._next_slot + 1) % PERSISTENT_NOTIFICATION_SLOTS
            self._on_slot_change(self._next_slot)
        recipients = self._configured_targets() if targets else []
        if notification_id is None and not recipients:
            return
        self._hass.async_create_task(
            self._async_send(notification_id, recipients, build), eager_start=False
        )

    async def _async_send(
        self,
        notification_id: str | None,
        recipients: list[tuple[int, NotifyTarget]],
        build: MessageBuilder,
    ) -> None:
        """Build the texts and deliver them; a failing target does not stop the others."""
        translations = await async_get_translations(
            self._hass, self._hass.config.language, "selector", integrations=[DOMAIN]
        )
        title, message = build(Texts(translations))
        if notification_id is not None:
            persistent_notification.async_create(
                self._hass, message, title=title, notification_id=notification_id
            )
        for number, target in recipients:
            if not target_present(self._hass, target):
                self._on_target_check(number, target, False)
                continue
            try:
                if target.kind == NOTIFY_TARGET_ENTITY:
                    await self._hass.services.async_call(
                        NOTIFY_DOMAIN,
                        NOTIFY_SERVICE_SEND_MESSAGE,
                        {"entity_id": target.target, "title": title, "message": message},
                        blocking=True,
                    )
                else:
                    await self._hass.services.async_call(
                        NOTIFY_DOMAIN,
                        service_name(target),
                        {"title": title, "message": message},
                        blocking=True,
                    )
            except HomeAssistantError, vol.Invalid:
                _LOGGER.warning("Sending a notification to %s failed", target.target, exc_info=True)
