"""Tests for the yearly session store."""

from __future__ import annotations

import asyncio
import os
from typing import Any
from unittest.mock import patch

import pytest
from custom_components.ev_charging.const import store_key_sessions
from custom_components.ev_charging.models import Session
from custom_components.ev_charging.store import (
    SessionYearStore,
    _backup_store_file,
    async_list_session_years,
)
from homeassistant.core import HomeAssistant


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Give this module's hass a private config dir instead of the shared default.

    async_list_session_years and the migration backup touch real files
    directly; the plugin's default config dir is a fixed path shared by
    every test in the run, so real files written there would leak between
    tests.
    """
    return hass_tmp_config_dir


def _session(session_id: str) -> Session:
    return Session(
        id=session_id,
        location="home",
        plug_start="2026-09-05T18:12:04+02:00",
        identification_source="unresolved",
    )


async def test_load_returns_empty_list_when_no_file_exists(hass: HomeAssistant) -> None:
    """A year that was never saved loads as an empty list, not an error."""
    store = SessionYearStore(hass, 2026)
    assert await store.async_load() == []


async def test_sessions_round_trip_through_save_and_load(hass: HomeAssistant) -> None:
    """Saved sessions load back unchanged."""
    store = SessionYearStore(hass, 2026)
    sessions = [_session("2026-01-05T14:39:00_v001"), _session("2026-01-11T11:56:00_v001")]

    await store.async_save(sessions)

    assert await store.async_load() == sessions


async def test_save_replaces_the_full_year(hass: HomeAssistant) -> None:
    """A second save replaces the previous content rather than appending to it."""
    store = SessionYearStore(hass, 2026)
    await store.async_save([_session("a")])

    await store.async_save([_session("b")])

    assert [session.id for session in await store.async_load()] == ["b"]


async def test_concurrent_saves_do_not_interleave(hass: HomeAssistant) -> None:
    """Two concurrent saves on the same year each fully apply, never mixed (I9).

    Each save goes through its own SessionYearStore instance, as two
    independent call sites would, so this only passes if the lock is shared
    per year rather than held by a single instance.
    """
    first = [_session("first-a"), _session("first-b")]
    second = [_session("second-a"), _session("second-b")]

    await asyncio.gather(
        SessionYearStore(hass, 2026).async_save(first),
        SessionYearStore(hass, 2026).async_save(second),
    )

    loaded_ids = {session.id for session in await SessionYearStore(hass, 2026).async_load()}
    assert loaded_ids == {"first-a", "first-b"} or loaded_ids == {"second-a", "second-b"}


def _touch_year_files(storage_dir: str, years: list[int]) -> None:
    """Create empty files at the real paths a Store would write to on disk.

    Store I/O is mocked to an in-memory dict under the test harness, so
    exercising the directory scan itself needs real files placed directly.
    """
    os.makedirs(storage_dir, exist_ok=True)
    for year in years:
        open(os.path.join(storage_dir, store_key_sessions(year)), "w", encoding="utf-8").close()


async def test_async_list_session_years_finds_existing_stores(hass: HomeAssistant) -> None:
    """Only years with an actual store file are reported."""
    await hass.async_add_executor_job(_touch_year_files, hass.config.path(".storage"), [2025, 2026])

    assert await async_list_session_years(hass) == [2025, 2026]


async def test_async_list_session_years_empty_without_storage_dir(hass: HomeAssistant) -> None:
    """No .storage directory yet means no years, not an error."""
    assert await async_list_session_years(hass) == []


def test_backup_store_file_copies_existing_file_aside(tmp_path: Any) -> None:
    """The pre-migration file survives unchanged at a version-tagged path."""
    path = tmp_path / "ev_charging.sessions_2026"
    path.write_text('{"version": 1, "minor_version": 0, "data": {}}', encoding="utf-8")

    _backup_store_file(str(path), old_major_version=1, old_minor_version=0)

    backup_path = tmp_path / "ev_charging.sessions_2026.v1.0.bak"
    assert backup_path.read_text(encoding="utf-8") == path.read_text(encoding="utf-8")


def test_backup_store_file_does_nothing_when_file_is_missing(tmp_path: Any) -> None:
    """A store that has never been written yet has nothing to back up."""
    path = tmp_path / "ev_charging.sessions_2026"

    _backup_store_file(str(path), old_major_version=1, old_minor_version=0)

    assert list(tmp_path.iterdir()) == []


async def test_migration_backs_up_before_writing(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Loading a store at an older schema version triggers the backup (6.1)."""
    key = store_key_sessions(2026)
    hass_storage[key] = {"version": 1, "minor_version": 0, "data": {"sessions": []}}

    with patch("custom_components.ev_charging.store._backup_store_file") as backup:
        await SessionYearStore(hass, 2026).async_load()

    assert backup.call_count == 1
    _path, old_major, old_minor = backup.call_args[0]
    assert (old_major, old_minor) == (1, 0)
