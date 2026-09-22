"""Tests for the reverse geocoding lookup and its rate limit (7.7)."""

from __future__ import annotations

import asyncio

import pytest
from custom_components.ev_charging import geocoding
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

URL = "https://nominatim.openstreetmap.org/reverse"


async def test_a_successful_lookup_returns_the_address(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A 200 response with a display_name is returned as the address."""
    aioclient_mock.get(URL, json={"display_name": "Marienplatz, München"})

    address = await geocoding.async_get_queue(hass).async_lookup(
        hass, url=URL, contact="test@example.invalid", latitude=48.1, longitude=11.6
    )

    assert address == "Marienplatz, München"


async def test_an_error_status_yields_no_address(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A non-200 response never raises; it yields None instead."""
    aioclient_mock.get(URL, status=503)

    address = await geocoding.async_get_queue(hass).async_lookup(
        hass, url=URL, contact="test@example.invalid", latitude=48.1, longitude=11.6
    )

    assert address is None


async def test_a_response_without_a_display_name_yields_no_address(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A malformed or empty answer is treated as no address, not as a crash."""
    aioclient_mock.get(URL, json={"error": "Unable to geocode"})

    address = await geocoding.async_get_queue(hass).async_lookup(
        hass, url=URL, contact="test@example.invalid", latitude=48.1, longitude=11.6
    )

    assert address is None


async def test_the_contact_is_sent_in_the_user_agent(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """The configured contact reaches the service, as its usage policy requires."""
    aioclient_mock.get(URL, json={"display_name": "Somewhere"})

    await geocoding.async_get_queue(hass).async_lookup(
        hass, url=URL, contact="someone@example.invalid", latitude=48.1, longitude=11.6
    )

    (call,) = aioclient_mock.mock_calls
    headers = call[3]
    assert "someone@example.invalid" in headers["User-Agent"]


async def test_the_queue_is_shared_across_calls(hass: HomeAssistant) -> None:
    """The same hass always gets the same queue, so its rate limit applies globally."""
    assert geocoding.async_get_queue(hass) is geocoding.async_get_queue(hass)


async def test_the_queue_serializes_overlapping_lookups(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two lookups through the same queue never run at the same time."""
    concurrent = 0
    peak = 0

    async def _fake_fetch(
        hass: HomeAssistant, *, url: str, contact: str, latitude: float, longitude: float
    ) -> str | None:
        nonlocal concurrent, peak
        concurrent += 1
        peak = max(peak, concurrent)
        await asyncio.sleep(0)
        concurrent -= 1
        return "ok"

    monkeypatch.setattr(geocoding, "_async_fetch", _fake_fetch)
    queue = geocoding.async_get_queue(hass)

    await asyncio.gather(
        queue.async_lookup(hass, url=URL, contact="a", latitude=1, longitude=1),
        queue.async_lookup(hass, url=URL, contact="a", latitude=2, longitude=2),
    )

    assert peak == 1
