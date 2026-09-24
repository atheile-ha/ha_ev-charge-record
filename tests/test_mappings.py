"""Tests for loading, validating and looking up device mapping files (4.7)."""

import copy
import json

import pytest
from custom_components.ev_charging import mappings
from custom_components.ev_charging.const import SUBENTRY_TYPE_VEHICLE, SUBENTRY_TYPE_WALLBOX
from homeassistant.core import HomeAssistant

SHIPPED_IDS = {
    "openems_keba_p40",
    "openems_keba_kecontact_udp",
    "openems_webasto_next",
    "openems_spelsberg_smart",
    "openems_abl_emh",
    "openems_alfen",
    "openems_hardybarth",
    "openems_heidelberg_connect",
    "openems_mennekes",
    "mbapi2020_mercedes_me",
    "myskoda_skoda",
}


def test_all_shipped_mapping_files_load_without_error() -> None:
    """Every mapping file shipped with the integration passes validation."""
    loaded = mappings.load_all(mappings.MAPPINGS_DIR)

    assert set(loaded) == SHIPPED_IDS


def test_keba_p40_plug_state_and_error_match_the_concept() -> None:
    """The KEBA P40 mapping carries the exact values from chapter 4.7."""
    loaded = mappings.load_all(mappings.MAPPINGS_DIR)
    keba = loaded["openems_keba_p40"]

    assert keba.kind == SUBENTRY_TYPE_WALLBOX
    assert keba.role_values("plug_state") == {
        "undefined": "neutral",
        "unplugged": "not_connected",
        "plugged_on_wallbox_not_ev": "not_connected",
        "plugged_on_wallbox_and_locked_not_ev": "not_connected",
        "plugged_not_locked_on_ev": "connected",
        "plugged_and_locked": "connected",
    }
    assert keba.role_values("error") == {
        "undefined": "neutral",
        "start-up_of_the_charging_station": "ok",
        "not_ready_for_charging": "ok",
        "ready_for_charging_waiting_for_ev": "ok",
        "charging": "ok",
        "error": "error",
        "charging_is_temporarily_interrupted": "ok",
    }
    assert keba.roles["plug_state"].note_key == "cable_variant"
    assert keba.roles["identification"].register is not None
    assert keba.role_values("identification") == {}


def test_mercedes_me_charge_state_and_type_match_the_concept() -> None:
    """The Mercedes Me mapping carries the exact values from chapter 4.7, error is neutral."""
    loaded = mappings.load_all(mappings.MAPPINGS_DIR)
    mercedes = loaded["mbapi2020_mercedes_me"]

    assert mercedes.kind == SUBENTRY_TYPE_VEHICLE
    charge_state = mercedes.role_values("charge_state")
    assert charge_state["11"] == "charging"
    assert charge_state["3"] == "disconnected"
    assert charge_state["error"] == "neutral"
    charge_type = mercedes.role_values("charge_type")
    assert charge_type["13"] == "ac"
    assert charge_type["11"] == "dc"
    assert charge_type["9"] == "neutral"
    assert charge_type["error"] == "neutral"


def test_mercedes_me_plug_state_reads_the_charge_inlet_coupler() -> None:
    """Only "vehicle not plugged" is not connected, the neutral value keeps the last class."""
    loaded = mappings.load_all(mappings.MAPPINGS_DIR)

    assert loaded["mbapi2020_mercedes_me"].role_values("plug_state") == {
        "vehicle not plugged": "not_connected",
        "vehicle plugged": "connected",
        "plugged": "connected",
        "error": "neutral",
    }


def test_skoda_charge_state_and_plug_state_match_the_concept() -> None:
    """The Škoda mapping's charge_state, charge_type and plug_state match chapter 4.7.

    connect_cable is deliberately connected_idle, not disconnected: the
    source integration's own maintainers confirmed it fires while the cable
    is physically connected but no power is flowing.
    """
    loaded = mappings.load_all(mappings.MAPPINGS_DIR)
    skoda = loaded["myskoda_skoda"]

    assert skoda.kind == SUBENTRY_TYPE_VEHICLE
    assert skoda.role_values("charge_state") == {
        "ready_for_charging": "connected_idle",
        "connect_cable": "connected_idle",
        "conserving": "connected_idle",
        "charging": "charging",
        "charging_interrupted": "connected_idle",
        "error": "error",
    }
    assert skoda.role_values("charge_type") == {"ac": "ac", "dc": "dc", "off": "neutral"}
    assert skoda.role_values("plug_state") == {"on": "connected", "off": "not_connected"}


def test_malformed_file_is_skipped(tmp_path) -> None:
    """A file that is not valid JSON is skipped, the rest still load."""
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    _write_minimal(tmp_path / "good.json", mapping_id="good_one")

    loaded = mappings.load_all(tmp_path)

    assert set(loaded) == {"good_one"}


def test_file_with_invalid_class_is_skipped(tmp_path) -> None:
    """A role value outside its allowed class set invalidates the whole file."""
    _write_minimal(tmp_path / "bad.json", mapping_id="bad_one", plug_state_class="not_a_class")

    loaded = mappings.load_all(tmp_path)

    assert loaded == {}


def test_duplicate_id_across_two_files_drops_both(tmp_path) -> None:
    """Two files sharing an id are both skipped: the id is the only way to tell devices apart."""
    _write_minimal(tmp_path / "a.json", mapping_id="dupe")
    _write_minimal(tmp_path / "b.json", mapping_id="dupe")
    _write_minimal(tmp_path / "c.json", mapping_id="unique_one")

    loaded = mappings.load_all(tmp_path)

    assert set(loaded) == {"unique_one"}


def test_mappings_for_kind_filters_and_sorts_by_label() -> None:
    """mappings_for_kind returns only the requested kind, sorted by device label."""
    loaded = mappings.load_all(mappings.MAPPINGS_DIR)

    wallboxes = mappings.mappings_for_kind(loaded, SUBENTRY_TYPE_WALLBOX)
    vehicles = mappings.mappings_for_kind(loaded, SUBENTRY_TYPE_VEHICLE)

    assert all(m.kind == SUBENTRY_TYPE_WALLBOX for m in wallboxes)
    assert all(m.kind == SUBENTRY_TYPE_VEHICLE for m in vehicles)
    assert [m.device_label for m in wallboxes] == sorted(m.device_label for m in wallboxes)
    assert len(wallboxes) + len(vehicles) == len(SHIPPED_IDS)


async def test_async_get_mappings_caches_across_calls(hass: HomeAssistant, monkeypatch) -> None:
    """The mapping table is loaded once and reused from hass.data."""
    calls = []
    original = mappings.load_all

    def _counting_load_all(directory):
        calls.append(directory)
        return original(directory)

    monkeypatch.setattr(mappings, "load_all", _counting_load_all)

    first = await mappings.async_get_mappings(hass)
    second = await mappings.async_get_mappings(hass)

    assert first is second
    assert len(calls) == 1


def _write_minimal(path, *, mapping_id: str, plug_state_class: str = "not_connected") -> None:
    """Write a minimal, otherwise-valid wallbox mapping file for validation tests."""
    path.write_text(
        json.dumps(
            {
                "format_version": 1,
                "id": mapping_id,
                "kind": SUBENTRY_TYPE_WALLBOX,
                "integration": {
                    "domain": "openems",
                    "name": "Test",
                    "short_name": "Test",
                    "min_version": "1.0.0",
                },
                "device": {"manufacturer": "Test", "model": "Model"},
                "roles": {
                    "plug_state": {"values": {"a": plug_state_class}},
                },
            }
        ),
        encoding="utf-8",
    )


VALID_REGISTER = {
    "function_code": 3,
    "address": 1500,
    "count": 2,
    "unit_id_default": 255,
    "decode": "uint32_big_endian_word_order",
    "format": "hex_upper_8",
}


def _write_register_mapping(path, *, mapping_id: str = "with_register", **changes) -> None:
    """Write a wallbox mapping whose identification role reads a register."""
    register = {**copy.deepcopy(VALID_REGISTER), **changes}
    path.write_text(
        json.dumps(
            {
                "format_version": 1,
                "id": mapping_id,
                "kind": "wallbox",
                "integration": {
                    "domain": "openems",
                    "name": "Test",
                    "short_name": "Test",
                    "min_version": "1.0.0",
                },
                "device": {"manufacturer": "Test", "model": "Model"},
                "roles": {"identification": {"register": register}},
            }
        ),
        encoding="utf-8",
    )


def test_the_keba_p40_reads_the_identification_from_register_1500() -> None:
    """The shipped mapping describes register 1500 as two words, read with function code 3."""
    keba = mappings.load_all(mappings.MAPPINGS_DIR)["openems_keba_p40"]

    assert keba.role_register("identification") == VALID_REGISTER
    assert keba.role_register("plug_state") is None
    assert keba.role_register("missing_role") is None


def test_only_the_keba_p40_carries_a_register() -> None:
    """No other shipped device has a register."""
    loaded = mappings.load_all(mappings.MAPPINGS_DIR)

    assert {
        mapping_id
        for mapping_id, mapping in loaded.items()
        if mapping.role_register("identification") is not None
    } == {"openems_keba_p40"}


def test_a_valid_register_entry_loads(tmp_path) -> None:
    """A register entry with the supported function code, decoding and format is accepted."""
    _write_register_mapping(tmp_path / "ok.json")

    assert set(mappings.load_all(tmp_path)) == {"with_register"}


@pytest.mark.parametrize("function_code", [1, 2, 4, 5, 6, 16, "3", True, None])
def test_a_register_that_is_not_read_with_function_code_3_is_rejected(
    tmp_path, function_code
) -> None:
    """Only reading holding registers can be expressed; anything else, above all a write, cannot."""
    _write_register_mapping(tmp_path / "bad.json", function_code=function_code)

    assert mappings.load_all(tmp_path) == {}


@pytest.mark.parametrize(
    "changes",
    [
        {"address": -1},
        {"address": 65536},
        {"address": "1500"},
        {"address": True},
        {"count": 0},
        {"count": 3},
        {"count": 1},
        {"decode": "int32_little_endian"},
        {"format": "decimal"},
        {"unit_id_default": 256},
        {"unit_id_default": -1},
    ],
)
def test_a_register_entry_outside_what_the_reader_supports_is_rejected(tmp_path, changes) -> None:
    """A file describing a register the reader cannot handle is skipped as a whole."""
    _write_register_mapping(tmp_path / "bad.json", **changes)

    assert mappings.load_all(tmp_path) == {}


def test_a_register_entry_needs_its_fields(tmp_path) -> None:
    """A register entry with a field missing is rejected."""
    path = tmp_path / "bad.json"
    _write_register_mapping(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["roles"]["identification"]["register"]["decode"]
    path.write_text(json.dumps(data), encoding="utf-8")

    assert mappings.load_all(tmp_path) == {}


def test_a_role_other_than_the_identification_cannot_read_a_register(tmp_path) -> None:
    """Registers are only for the identification role."""
    path = tmp_path / "bad.json"
    _write_register_mapping(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["roles"]["plug_state"] = {"register": VALID_REGISTER}
    path.write_text(json.dumps(data), encoding="utf-8")

    assert mappings.load_all(tmp_path) == {}
