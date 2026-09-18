"""Session store: one Store per year, locked writes, schema migration (6.1)."""

from __future__ import annotations

import logging
import os
import re
import shutil
from asyncio import Lock
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    STORAGE_MINOR_VERSION_SESSIONS,
    STORAGE_VERSION_SESSIONS,
    store_key_sessions,
)
from .models import Session

_LOGGER = logging.getLogger(__name__)

_SESSIONS_FILENAME_RE = re.compile(r"^ev_charging\.sessions_(\d{4})$")
_DATA_YEAR_STORES = "session_year_stores"


def _backup_store_file(path: str, old_major_version: int, old_minor_version: int) -> None:
    """Copy a store file aside before it is overwritten by a migration.

    Does nothing if the file does not exist, which is the normal case for a
    store that has never been migrated before.
    """
    if not os.path.exists(path):
        return
    shutil.copy2(path, f"{path}.v{old_major_version}.{old_minor_version}.bak")


class _MigratingStore(Store[dict[str, Any]]):
    """A Store that backs up its file before applying a schema migration."""

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict[str, Any]
    ) -> dict[str, Any]:
        await self.hass.async_add_executor_job(
            _backup_store_file, self.path, old_major_version, old_minor_version
        )
        _LOGGER.info(
            "Migrating %s from schema %s.%s to %s.%s",
            self.key,
            old_major_version,
            old_minor_version,
            self.version,
            self.minor_version,
        )
        return old_data


class SessionYearStore:
    """Access to one year's sessions. async_save is the only write path (I9).

    Every call site for the same year shares one lock and one underlying
    Store, obtained through `SessionYearStore(hass, year)`; the lock created
    by one caller would otherwise not be seen by another.
    """

    def __init__(self, hass: HomeAssistant, year: int) -> None:
        """Return the shared store for a given year, creating it on first use."""
        year_stores = hass.data.setdefault(DOMAIN, {}).setdefault(_DATA_YEAR_STORES, {})
        if year not in year_stores:
            year_stores[year] = (
                _MigratingStore(
                    hass,
                    STORAGE_VERSION_SESSIONS,
                    store_key_sessions(year),
                    minor_version=STORAGE_MINOR_VERSION_SESSIONS,
                ),
                Lock(),
            )
        self._store, self._lock = year_stores[year]

    async def async_load(self) -> list[Session]:
        """Return the sessions of this year, empty if none were ever saved."""
        data = await self._store.async_load()
        if data is None:
            return []
        return [Session.from_dict(item) for item in data.get("sessions", [])]

    async def async_save(self, sessions: list[Session]) -> None:
        """Replace the full session list of this year."""
        async with self._lock:
            await self._store.async_save({"sessions": [session.to_dict() for session in sessions]})


async def async_list_session_years(hass: HomeAssistant) -> list[int]:
    """Return the years for which a session store file exists on disk."""

    def _scan() -> list[int]:
        storage_dir = hass.config.path(".storage")
        if not os.path.isdir(storage_dir):
            return []
        years = []
        for filename in os.listdir(storage_dir):
            match = _SESSIONS_FILENAME_RE.match(filename)
            if match:
                years.append(int(match.group(1)))
        return sorted(years)

    return await hass.async_add_executor_job(_scan)
