"""A stand-in for the Modbus client library, scripted per read."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

import pytest
from custom_components.ev_charging import direct_read

OK = "ok"
NO_CONNECTION = "no_connection"
CONNECT_ERROR = "connect_error"
MODBUS_ERROR = "modbus_error"
ERROR_RESPONSE = "error_response"
SHORT_RESPONSE = "short_response"
NO_REPLY = "no_reply"


class FakeModbusError(Exception):
    """Stands in for the library's base exception."""


def registers_for(card: str) -> list[int]:
    """Return the two register words that hold a card identifier of eight hex digits."""
    value = int(card, 16)
    return [value >> 16, value & 0xFFFF]


class FakeResponse:
    """The reply to a read."""

    def __init__(self, registers: list[int], *, error: bool = False) -> None:
        """Hold the register words."""
        self.registers = registers
        self._error = error

    def isError(self) -> bool:
        """Return whether the device answered with an error."""
        return self._error


class FakeClient:
    """A client that does what its script says and refuses any call but the three it may get."""

    def __init__(self, device: FakeDevice, host: str, kwargs: dict[str, Any]) -> None:
        """Take the next scripted outcome."""
        self.device = device
        self.host = host
        self.kwargs = kwargs
        self.calls: list[str] = []
        self.outcome = device.next_outcome()

    def __getattr__(self, name: str) -> Any:
        """Fail for every method that is not implemented here, above all any write."""
        raise AssertionError(f"unexpected call on the Modbus client: {name}")

    async def connect(self) -> bool:
        """Connect, or fail as scripted."""
        self.calls.append("connect")
        kind = self.outcome[0]
        if kind == NO_CONNECTION:
            return False
        if kind == CONNECT_ERROR:
            raise OSError("connection refused")
        return True

    async def read_holding_registers(
        self, address: int, *, count: int = 1, device_id: int = 1
    ) -> FakeResponse:
        """Read, or fail as scripted."""
        self.calls.append("read_holding_registers")
        self.device.reads.append((address, count, device_id))
        kind = self.outcome[0]
        if kind == MODBUS_ERROR:
            raise FakeModbusError("device failure")
        if kind == NO_REPLY:
            await asyncio.sleep(3600)
        if kind == ERROR_RESPONSE:
            return FakeResponse([], error=True)
        registers = list(self.outcome[1])
        if kind == SHORT_RESPONSE:
            registers = registers[:1]
        return FakeResponse(registers)

    def close(self) -> None:
        """Close the connection."""
        self.calls.append("close")


class FakeDevice:
    """The device behind the fake library: scripted outcomes, and a record of what happened."""

    def __init__(self, outcomes: Iterable[tuple[Any, ...]]) -> None:
        """Script the outcome of each read in turn; the last one repeats."""
        self.outcomes = list(outcomes)
        self.clients: list[FakeClient] = []
        self.reads: list[tuple[int, int, int]] = []
        self.imports = 0
        self._next = 0

    def next_outcome(self) -> tuple[Any, ...]:
        """Return the outcome for the next client."""
        outcome = self.outcomes[min(self._next, len(self.outcomes) - 1)]
        self._next += 1
        return outcome

    def make_client(self, host: str, **kwargs: Any) -> FakeClient:
        """Create a client, like the library's class does."""
        client = FakeClient(self, host, kwargs)
        self.clients.append(client)
        return client

    def import_backend(self) -> direct_read._Backend:
        """Stand in for importing the library."""
        self.imports += 1
        return direct_read._Backend(self.make_client, (FakeModbusError, OSError, TimeoutError))


def install(monkeypatch: pytest.MonkeyPatch, device: FakeDevice) -> FakeDevice:
    """Make the integration use the fake library."""
    monkeypatch.setattr(direct_read, "_import_backend", device.import_backend)
    return device
