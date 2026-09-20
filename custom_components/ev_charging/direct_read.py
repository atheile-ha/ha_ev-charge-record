"""Read-only Modbus TCP access to the wallbox.

This is the only module that talks to a device directly. It reads holding
registers (function code 3) and nothing else: it holds no function that
writes, and it calls only connect, read_holding_registers and close on the
client. A caller passes the connection details and the register description
and gets the register's value; what the value means is decided elsewhere.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    DIRECT_READ_TIMEOUT_S,
    DOMAIN,
    REGISTER_DECODE_UINT32_BIG_ENDIAN,
    REGISTER_FORMAT_HEX_UPPER_8,
)

_LOGGER = logging.getLogger(__name__)

_DATA_BACKEND = "direct_read_backend"


@dataclass(frozen=True, slots=True)
class Endpoint:
    """Where the device listens."""

    host: str
    port: int
    unit_id: int


@dataclass(frozen=True, slots=True)
class RegisterSpec:
    """Which registers to read and how to turn them into one value."""

    address: int
    count: int
    decode: str
    output: str


@dataclass(frozen=True, slots=True)
class _Backend:
    """The Modbus client library, imported on first use."""

    client_class: Any
    errors: tuple[type[BaseException], ...]


def _import_backend() -> _Backend:
    """Import the Modbus client library. Blocking; run in the executor."""
    from pymodbus.client import AsyncModbusTcpClient
    from pymodbus.exceptions import ModbusException

    return _Backend(AsyncModbusTcpClient, (ModbusException, OSError, TimeoutError))


async def _async_backend(hass: HomeAssistant) -> _Backend:
    """Return the Modbus client library, importing it once outside the event loop."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    backend = domain_data.get(_DATA_BACKEND)
    if backend is None:
        backend = await hass.async_add_executor_job(_import_backend)
        domain_data[_DATA_BACKEND] = backend
    return backend


async def async_prepare(hass: HomeAssistant) -> None:
    """Import the Modbus client library, outside the event loop.

    Called when a wallbox is set up for reading the device; without that the
    library is never imported.
    """
    await _async_backend(hass)


def decode_registers(registers: Sequence[int], decode: str) -> int | None:
    """Combine register words into one unsigned value, or None for an unknown decoding."""
    if decode == REGISTER_DECODE_UINT32_BIG_ENDIAN and len(registers) == 2:
        return (registers[0] << 16) | registers[1]
    return None


def format_value(value: int, output: str) -> str | None:
    """Render a decoded value as text, or None for an unknown format."""
    if output == REGISTER_FORMAT_HEX_UPPER_8:
        return f"{value:08X}"
    return None


async def async_read_register(
    hass: HomeAssistant, endpoint: Endpoint, spec: RegisterSpec
) -> int | None:
    """Read one register value from the device.

    Connects, reads once and closes the connection again. Returns None when
    the device gives no valid answer: no connection, no reply in time, an
    error reply or a reply of the wrong length. Never raises for those.

    Every step is traced on the debug level: where it was read, how long it
    took and how the device answered. The register values themselves are
    never written to the log.
    """
    backend = await _async_backend(hass)
    client = backend.client_class(
        endpoint.host,
        port=endpoint.port,
        timeout=DIRECT_READ_TIMEOUT_S,
        retries=0,
        reconnect_delay=0,
    )
    started = hass.loop.time()
    target = f"{endpoint.host}:{endpoint.port}, unit {endpoint.unit_id}, register {spec.address}"
    try:
        async with asyncio.timeout(2 * DIRECT_READ_TIMEOUT_S):
            if not await client.connect():
                _LOGGER.debug(
                    "Read of %s: no connection after %.1f s", target, hass.loop.time() - started
                )
                return None
            response = await client.read_holding_registers(
                spec.address, count=spec.count, device_id=endpoint.unit_id
            )
    except backend.errors as err:
        _LOGGER.debug(
            "Read of %s failed after %.1f s: %s %s",
            target,
            hass.loop.time() - started,
            type(err).__name__,
            err,
        )
        return None
    finally:
        client.close()

    elapsed = hass.loop.time() - started
    if response.isError():
        _LOGGER.debug(
            "Read of %s: the device answered with an error (%s) after %.1f s",
            target,
            response,
            elapsed,
        )
        return None
    value = decode_registers(response.registers, spec.decode)
    _LOGGER.debug(
        "Read of %s: %d registers came back after %.1f s%s",
        target,
        len(response.registers),
        elapsed,
        "" if value is not None else ", which cannot be decoded",
    )
    return value
