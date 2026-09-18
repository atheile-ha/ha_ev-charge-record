"""Tests for the yearly session store."""

from __future__ import annotations

import asyncio
import json
import os

from custom_components.ev_charging.models import Session
from custom_components.ev_charging.store import SessionYearStore, async_list_session_years
from homeassistant.core import HomeAssistant


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


async def test_async_list_session_years_finds_existing_stores(hass: HomeAssistant) -> None:
    """Only years with an actual store file are reported."""
    await SessionYearStore(hass, 2025).async_save([_session("x")])
    await SessionYearStore(hass, 2026).async_save([_session("y")])

    assert await async_list_session_years(hass) == [2025, 2026]


async def test_async_list_session_years_empty_without_storage_dir(hass: HomeAssistant) -> None:
    """No .storage directory yet means no years, not an error."""
    assert await async_list_session_years(hass) == []


def _write_legacy_file(storage_dir: str) -> str:
    """Write a store file at an older minor version, return its path."""
    os.makedirs(storage_dir, exist_ok=True)
    path = os.path.join(storage_dir, "ev_charging.sessions_2026")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "version": 1,
                "minor_version": 0,
                "key": "ev_charging.sessions_2026",
                "data": {"sessions": []},
            },
            handle,
        )
    return path


async def test_migration_backs_up_the_old_file_before_writing(hass: HomeAssistant) -> None:
    """A schema migration keeps a copy of the pre-migration file (6.1)."""
    path = await hass.async_add_executor_job(_write_legacy_file, hass.config.path(".storage"))

    store = SessionYearStore(hass, 2026)
    await store.async_load()

    assert await hass.async_add_executor_job(os.path.exists, f"{path}.v1.0.bak")
