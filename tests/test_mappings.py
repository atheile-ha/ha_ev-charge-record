"""Tests for loading, validating and looking up device mapping files (4.7)."""

import json

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
