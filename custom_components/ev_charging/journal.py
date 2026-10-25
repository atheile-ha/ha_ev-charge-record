"""Journal of the events and decisions of the session capture.

An entry is added synchronously in the event loop, waits for nothing and
never raises. Entries are kept in memory and written to the journal store at
the persist interval and on unload, only when something new was added. A
failed write keeps them in memory and is retried; it never reaches the
caller. Card ids appear shortened to their last characters; vin, card label,
address and coordinates never appear.
"""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    JOURNAL_ADMIN_ACTION,
    JOURNAL_CARD_DIGITS,
    JOURNAL_EXCLUDED_FIELDS,
    JOURNAL_MAX_ENTRIES,
    JOURNAL_PRUNE_INTERVAL_H,
    JOURNAL_RETENTION_DAYS,
    PERSIST_INTERVAL_S,
)
from .store import JournalStore

_LOGGER = logging.getLogger(__name__)

_DATA_JOURNAL = "journal"
_CARD_FIELD = "card_uid"


def shorten_card(value: str | None) -> str | None:
    """Return a card id cut down to its last characters."""
    if not value:
        return value
    return str(value)[-JOURNAL_CARD_DIGITS:]


def sanitize(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return the details of an entry without the fields that must not appear.

    Nested mappings are cleaned the same way. A card id is shortened.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key in JOURNAL_EXCLUDED_FIELDS:
            continue
        if key == _CARD_FIELD:
            value = shorten_card(value)
        elif isinstance(value, Mapping):
            value = sanitize(value)
        result[key] = value
    return result


def _entry_time(entry: Mapping[str, Any]) -> datetime | None:
    """Return the moment of an entry, None if it is unreadable."""
    value = entry.get("time")
    return dt_util.parse_datetime(value) if isinstance(value, str) else None


def prune(entries: Iterable[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    """Return the entries within the retention time, at most the limit, the newest kept.

    An entry without a readable time is dropped. The order is kept.
    """
    cutoff = now - timedelta(days=JOURNAL_RETENTION_DAYS)
    kept = [
        entry
        for entry in entries
        if (moment := _entry_time(entry)) is not None and moment >= cutoff
    ]
    return kept[-JOURNAL_MAX_ENTRIES:]


class Journal:
    """The entries of the running integration and their store."""

    def __init__(
        self, hass: HomeAssistant, entries: list[dict[str, Any]], *, changed: bool = False
    ) -> None:
        """Hold the loaded entries; changed marks them as differing from the store."""
        self._hass = hass
        self._store = JournalStore(hass)
        self._entries: deque[dict[str, Any]] = deque(entries, maxlen=JOURNAL_MAX_ENTRIES)
        self._dirty = changed
        self._unsubs: list[CALLBACK_TYPE] = []

    @property
    def entries(self) -> list[dict[str, Any]]:
        """Return the entries, oldest first."""
        return list(self._entries)

    def start(self) -> None:
        """Write at the persist interval and prune once a day."""
        self._unsubs.append(
            async_track_time_interval(
                self._hass, self._on_write_tick, timedelta(seconds=PERSIST_INTERVAL_S)
            )
        )
        self._unsubs.append(
            async_track_time_interval(
                self._hass, self._on_prune_tick, timedelta(hours=JOURNAL_PRUNE_INTERVAL_H)
            )
        )

    def stop(self) -> None:
        """Stop the timers."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    def add(self, entry: dict[str, Any]) -> None:
        """Append an entry; the oldest falls out once the limit is reached."""
        self._entries.append(entry)
        self._dirty = True

    def prune(self) -> None:
        """Drop the entries beyond the retention time."""
        kept = prune(self._entries, dt_util.now())
        if len(kept) != len(self._entries):
            self._entries = deque(kept, maxlen=JOURNAL_MAX_ENTRIES)
            self._dirty = True

    async def async_clear(self) -> None:
        """Drop every entry and write the empty journal."""
        self._entries.clear()
        self._dirty = True
        await self.async_flush()

    async def async_flush(self) -> None:
        """Write the entries if something new was added; a failure is kept for the next try."""
        if not self._dirty:
            return
        self._dirty = False
        try:
            await self._store.async_save(list(self._entries))
        except Exception:
            self._dirty = True
            _LOGGER.warning(
                "The journal could not be written; its entries are kept and written later",
                exc_info=True,
            )

    @callback
    def _on_write_tick(self, _now: datetime) -> None:
        """Write the new entries without waiting for it."""
        if self._dirty:
            self._hass.async_create_task(self.async_flush(), eager_start=False)

    @callback
    def _on_prune_tick(self, _now: datetime) -> None:
        """Drop old entries once a day."""
        self.prune()


def _journal(hass: HomeAssistant) -> Journal | None:
    """Return the journal of the running integration, None while none is set up."""
    return hass.data.get(DOMAIN, {}).get(_DATA_JOURNAL)


async def async_setup(hass: HomeAssistant) -> None:
    """Load the stored entries, drop the old ones and start writing."""
    if _journal(hass) is not None:
        return
    try:
        stored = await JournalStore(hass).async_load()
    except Exception:
        _LOGGER.warning("The stored journal could not be read; it starts empty", exc_info=True)
        stored = []
    kept = prune(stored, dt_util.now())
    journal = Journal(hass, kept, changed=len(kept) != len(stored))
    hass.data.setdefault(DOMAIN, {})[_DATA_JOURNAL] = journal
    journal.start()


async def async_unload(hass: HomeAssistant) -> None:
    """Stop the journal and write what is new."""
    journal = hass.data.get(DOMAIN, {}).pop(_DATA_JOURNAL, None)
    if journal is None:
        return
    journal.stop()
    await journal.async_flush()


async def async_clear(hass: HomeAssistant) -> None:
    """Drop every entry of the journal."""
    journal = _journal(hass)
    if journal is not None:
        await journal.async_clear()


def entries(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Return the entries of the running journal, oldest first."""
    journal = _journal(hass)
    return journal.entries if journal is not None else []


@callback
def add(
    hass: HomeAssistant,
    event: str,
    *,
    wallbox_id: str | None = None,
    vehicle_id: str | None = None,
    session: datetime | None = None,
    **data: Any,
) -> None:
    """Add an entry of the given event type. Waits for nothing and never raises.

    session is the plug_start of the session the entry concerns. data holds
    the details of the event.
    """
    try:
        journal = _journal(hass)
        if journal is None:
            return
        entry: dict[str, Any] = {
            "time": dt_util.now().isoformat(timespec="milliseconds"),
            "event": event,
        }
        if wallbox_id is not None:
            entry["wallbox_id"] = wallbox_id
        if vehicle_id is not None:
            entry["vehicle_id"] = vehicle_id
        if session is not None:
            entry["session"] = dt_util.as_local(session).replace(microsecond=0).isoformat()
        details = sanitize(data)
        if details:
            entry["data"] = details
        journal.add(entry)
    except Exception:
        _LOGGER.warning("A journal entry could not be added", exc_info=True)


@callback
def add_admin(
    hass: HomeAssistant,
    action: str,
    *,
    user_id: str | None,
    session_ids: Iterable[str] = (),
    fields: Iterable[str] = (),
    **data: Any,
) -> None:
    """Add the entry of a write by a service or a WebSocket command.

    Names the fields that changed, never their values.
    """
    add(
        hass,
        JOURNAL_ADMIN_ACTION,
        action=action,
        user_id=user_id,
        session_ids=list(session_ids),
        fields=sorted(fields),
        **data,
    )
