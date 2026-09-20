"""Tests for the read-only access to the wallbox."""

from __future__ import annotations

import ast
import asyncio
import socket
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace

import pytest
from custom_components.ev_charging import direct_read
from homeassistant.core import HomeAssistant

from tests.fake_modbus import (
    CONNECT_ERROR,
    ERROR_RESPONSE,
    MODBUS_ERROR,
    NO_CONNECTION,
    NO_REPLY,
    OK,
    SHORT_RESPONSE,
    FakeDevice,
    install,
    registers_for,
)

PACKAGE = Path(direct_read.__file__).parent
ENDPOINT = direct_read.Endpoint(host="192.0.2.10", port=502, unit_id=255)
SPEC = direct_read.RegisterSpec(
    address=1500, count=2, decode="uint32_big_endian_word_order", output="hex_upper_8"
)

# The client methods that put something on the wire to change the device.
MODBUS_WRITE_METHODS = {
    "write_coil",
    "write_coils",
    "write_register",
    "write_registers",
    "mask_write_register",
    "readwrite_registers",
    "write_file_record",
}


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _module_paths() -> list[Path]:
    return sorted(PACKAGE.glob("*.py"))


# ----------------------------------------------------------- what the code may not do


def test_no_module_calls_a_modbus_write() -> None:
    """Nothing in the integration names a method that writes to a Modbus device."""
    for path in _module_paths():
        for node in ast.walk(_tree(path)):
            name = node.attr if isinstance(node, ast.Attribute) else getattr(node, "id", None)
            assert name not in MODBUS_WRITE_METHODS, f"{path.name} uses {name}"


def test_the_reading_module_has_no_name_that_writes() -> None:
    """The module has no function, variable or attribute with write in its name."""
    for node in ast.walk(_tree(PACKAGE / "direct_read.py")):
        names = []
        if isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
        elif isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        for name in names:
            assert "write" not in name.lower(), name


def test_the_reading_module_only_connects_reads_and_closes() -> None:
    """The client is only ever asked to connect, read holding registers and close."""
    called = {
        node.func.attr
        for node in ast.walk(_tree(PACKAGE / "direct_read.py"))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "client"
    }

    assert called == {"connect", "read_holding_registers", "close"}


def test_only_the_resolver_uses_the_reading_module() -> None:
    """No module but the resolver imports the module that talks to the device."""
    for path in _module_paths():
        if path.name in ("direct_read.py", "resolver.py"):
            continue
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ImportFrom):
                imported = [alias.name for alias in node.names]
                assert node.module != "direct_read", path.name
                assert not (node.module is None and "direct_read" in imported), path.name


def test_no_module_imports_the_modbus_library_when_loaded() -> None:
    """The library is imported by the reading module when it is put to use, not at load."""
    for path in _module_paths():
        for node in _tree(path).body:
            if isinstance(node, ast.Import):
                assert not any(alias.name.startswith("pymodbus") for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("pymodbus"), path.name


# ------------------------------------------------------------------ decoding


def test_two_registers_make_one_unsigned_value_high_word_first() -> None:
    """Register 1500 is the high word, register 1501 the low word."""
    assert direct_read.decode_registers([0xD4CD, 0x7650], SPEC.decode) == 3570234960
    assert direct_read.decode_registers([0x0000, 0x0001], SPEC.decode) == 1
    assert direct_read.decode_registers([0xFFFF, 0xFFFF], SPEC.decode) == 0xFFFFFFFF


def test_a_decoding_needs_the_right_number_of_registers() -> None:
    """Too few registers, or an unknown decoding, yield no value."""
    assert direct_read.decode_registers([0xD4CD], SPEC.decode) is None
    assert direct_read.decode_registers([0xD4CD, 0x7650], "unknown") is None


def test_a_value_is_shown_as_eight_upper_case_hex_digits() -> None:
    """The identifier keeps its leading zeros."""
    assert direct_read.format_value(3570234960, SPEC.output) == "D4CD7650"
    assert direct_read.format_value(0x00ABCDEF, SPEC.output) == "00ABCDEF"
    assert direct_read.format_value(1, "unknown") is None


# ------------------------------------------------------------ reading with a fake


async def test_a_read_returns_the_decoded_value(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The register is read with function code 3 from the configured address and unit."""
    device = install(monkeypatch, FakeDevice([(OK, registers_for("D4CD7650"))]))

    value = await direct_read.async_read_register(hass, ENDPOINT, SPEC)

    assert value == 0xD4CD7650
    assert device.reads == [(1500, 2, 255)]
    client = device.clients[0]
    assert client.calls == ["connect", "read_holding_registers", "close"]
    assert client.host == "192.0.2.10"
    assert client.kwargs["port"] == 502


async def test_the_client_neither_retries_nor_reconnects_by_itself(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every access to the device is one the caller decided on."""
    device = install(monkeypatch, FakeDevice([(OK, registers_for("D4CD7650"))]))

    await direct_read.async_read_register(hass, ENDPOINT, SPEC)

    assert device.clients[0].kwargs["retries"] == 0
    assert device.clients[0].kwargs["reconnect_delay"] == 0


@pytest.mark.parametrize(
    "outcome",
    [
        (NO_CONNECTION,),
        (CONNECT_ERROR,),
        (MODBUS_ERROR, [0, 0]),
        (ERROR_RESPONSE,),
        (SHORT_RESPONSE, [1, 2]),
    ],
)
async def test_no_valid_answer_yields_none_and_closes_the_connection(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, outcome: tuple
) -> None:
    """A lost connection, an error or a short reply is a missing value, not an exception."""
    device = install(monkeypatch, FakeDevice([outcome]))

    assert await direct_read.async_read_register(hass, ENDPOINT, SPEC) is None

    assert device.clients[0].calls[-1] == "close"


async def test_a_reply_that_does_not_come_is_given_up_on(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A device that stays silent costs a bounded time, then the read fails."""
    monkeypatch.setattr(direct_read, "DIRECT_READ_TIMEOUT_S", 0.01)
    device = install(monkeypatch, FakeDevice([(NO_REPLY,)]))

    assert await direct_read.async_read_register(hass, ENDPOINT, SPEC) is None

    assert device.clients[0].calls == ["connect", "read_holding_registers", "close"]


async def test_each_read_opens_and_closes_its_own_connection(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The connection is not kept between reads."""
    device = install(monkeypatch, FakeDevice([(OK, registers_for("D4CD7650"))]))

    await direct_read.async_read_register(hass, ENDPOINT, SPEC)
    await direct_read.async_read_register(hass, ENDPOINT, SPEC)

    assert len(device.clients) == 2
    for client in device.clients:
        assert client.calls == ["connect", "read_holding_registers", "close"]


async def test_the_library_is_imported_once_and_only_when_needed(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing is imported until a read or the preparation asks for the library."""
    device = install(monkeypatch, FakeDevice([(OK, registers_for("D4CD7650"))]))
    assert device.imports == 0

    await direct_read.async_prepare(hass)
    await direct_read.async_read_register(hass, ENDPOINT, SPEC)
    await direct_read.async_read_register(hass, ENDPOINT, SPEC)

    assert device.imports == 1


# ----------------------------------------------------- reading from a real server


@pytest.fixture
async def modbus_server(socket_enabled: None) -> AsyncIterator[SimpleNamespace]:
    """A Modbus TCP server on the loopback interface, recording what it is asked."""
    pymodbus_server = pytest.importorskip("pymodbus.server")
    simulator = pytest.importorskip("pymodbus.simulator")
    functions: list[int] = []
    connections: list[bool] = []

    def _trace_pdu(sending: bool, pdu):
        functions.append(pdu.function_code)
        return pdu

    device = simulator.SimDevice(
        255,
        simdata=[
            simulator.SimData(1500, values=[0x1122, 0x3344], datatype=simulator.DataType.REGISTERS)
        ],
    )
    server = pymodbus_server.ModbusTcpServer(
        device,
        address=("127.0.0.1", 0),
        trace_pdu=_trace_pdu,
        trace_connect=connections.append,
    )
    await server.listen()
    port = server.transport.sockets[0].getsockname()[1]
    yield SimpleNamespace(port=port, functions=functions, connections=connections)
    await server.shutdown()


async def test_a_real_modbus_server_is_read_with_function_code_3_only(
    hass: HomeAssistant, modbus_server: SimpleNamespace
) -> None:
    """The library the integration ships with is used the way it expects, end to end."""
    endpoint = direct_read.Endpoint(host="127.0.0.1", port=modbus_server.port, unit_id=255)

    value = await direct_read.async_read_register(hass, endpoint, SPEC)
    await asyncio.sleep(0.3)

    assert value == 0x11223344
    assert direct_read.format_value(value, SPEC.output) == "11223344"
    assert set(modbus_server.functions) == {3}
    assert modbus_server.connections == [True, False]


async def test_a_refused_connection_yields_none(hass: HomeAssistant, socket_enabled: None) -> None:
    """Nothing listens on the port: the read fails cleanly."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    endpoint = direct_read.Endpoint(host="127.0.0.1", port=port, unit_id=255)

    assert await direct_read.async_read_register(hass, endpoint, SPEC) is None
