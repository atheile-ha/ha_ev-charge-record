"""Address lookup for external charging sessions, rate-limited (7.7).

The only outbound call this integration makes to a third party. A failure
never raises past this module: the caller gets None and tries again later.
"""

from __future__ import annotations

import asyncio
import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, GEOCODING_MIN_INTERVAL_S, GEOCODING_TIMEOUT_S

_LOGGER = logging.getLogger(__name__)

_DATA_QUEUE = "geocoding_queue"


async def _async_fetch(
    hass: HomeAssistant, *, url: str, contact: str, latitude: float, longitude: float
) -> str | None:
    """Perform one reverse-geocoding request. Never raises.

    Coordinates are personal data (I5) and are only ever logged truncated,
    and only on the debug level.
    """
    session = async_get_clientsession(hass)
    params = {"lat": f"{latitude:.5f}", "lon": f"{longitude:.5f}", "format": "jsonv2"}
    headers = {"User-Agent": f"ev_charging Home Assistant integration ({contact})"}
    try:
        async with asyncio.timeout(GEOCODING_TIMEOUT_S):
            response = await session.get(url, params=params, headers=headers)
            if response.status != 200:
                _LOGGER.debug("Geocoding request answered with status %s", response.status)
                return None
            data = await response.json(content_type=None)
    except Exception:
        _LOGGER.debug("Geocoding request failed", exc_info=True)
        return None
    address = data.get("display_name") if isinstance(data, dict) else None
    if isinstance(address, str) and address:
        return address
    _LOGGER.debug("Geocoding request returned no address")
    return None


class GeocodingQueue:
    """Serializes lookups so at most one request per second leaves the process."""

    def __init__(self) -> None:
        """Start with no prior request."""
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def async_lookup(
        self, hass: HomeAssistant, *, url: str, contact: str, latitude: float, longitude: float
    ) -> str | None:
        """Return the address for a coordinate, or None if the lookup failed.

        Waits out the rate limit under the lock, so two overlapping callers
        are still spaced apart by at least GEOCODING_MIN_INTERVAL_S.
        """
        async with self._lock:
            wait = GEOCODING_MIN_INTERVAL_S - (time.monotonic() - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                return await _async_fetch(
                    hass, url=url, contact=contact, latitude=latitude, longitude=longitude
                )
            finally:
                self._last = time.monotonic()


def async_get_queue(hass: HomeAssistant) -> GeocodingQueue:
    """Return the queue shared by every lookup, creating it on first use."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    queue = domain_data.get(_DATA_QUEUE)
    if queue is None:
        queue = GeocodingQueue()
        domain_data[_DATA_QUEUE] = queue
    return queue
