"""Tests for the ev_charging config flow."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.ev_charging.const import (
    DOMAIN,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
)
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

WALLBOX_INPUT: dict[str, Any] = {
    "name": "Carport",
    "current_type": "ac",
    "max_power_kw": 11.0,
    "roles": {
        "charge_power": "sensor.wallbox_power",
        "energy_total": "sensor.wallbox_energy_total",
        "energy_session": None,
        "plug_state": "sensor.wallbox_plug_state",
        "identification": None,
        "error": "binary_sensor.wallbox_error",
    },
    "expert": {
        "power_threshold_kw": 0.5,
        "start_debounce_s": 2,
        "identification_window_s": 15,
    },
}

VEHICLE_INPUT: dict[str, Any] = {
    "name": "GLB 250+ EQ",
    "active": True,
    "is_guest": False,
    "capacity_kwh": 85.0,
    "cost_mode": "dynamic",
    "cards": [{"uid": "ABC123", "label": "Karte GLB", "type": "rfid"}],
    "roles": {},
}

EXPECTED_HUB_SETTINGS: dict[str, Any] = {
    "update_interval_s": 30,
    "solar_valuation": "feed_in_tariff",
    "geocoding_enabled": True,
    "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
    "geocoding_contact": None,
    "estimate_uncertain_threshold_pct": 5,
    "grid_power": None,
    "grid_power_inverted": False,
    "grid_import": None,
    "grid_export": None,
    "price_grid": None,
    "price_grid_fixed": None,
    "price_feed_in": None,
    "price_feed_in_fixed": None,
}


@pytest.fixture(autouse=True)
def _source_entities(hass: HomeAssistant) -> None:
    """Provide plain (non-registry) states for the default role assignments."""
    hass.states.async_set("sensor.wallbox_power", "1.5", {"unit_of_measurement": "kW"})
    hass.states.async_set("sensor.wallbox_energy_total", "100.0", {"unit_of_measurement": "kWh"})
    hass.states.async_set("sensor.wallbox_energy_session", "1.0", {"unit_of_measurement": "kWh"})
    hass.states.async_set("sensor.wallbox_plug_state", "plugged_ev")
    hass.states.async_set("binary_sensor.wallbox_error", "off", {"device_class": "problem"})
    hass.states.async_set("sensor.wallbox_error_state", "0")
    hass.states.async_set("sensor.wallbox_identification", "0")
    hass.states.async_set("sensor.vehicle_soc", "80", {"unit_of_measurement": "%"})
    hass.states.async_set("sensor.vehicle_charge_state", "0")
    hass.states.async_set("sensor.vehicle_charge_type", "13")
    hass.states.async_set("device_tracker.vehicle", "home")
    hass.states.async_set("sensor.grid_power", "500", {"unit_of_measurement": "W"})


@pytest.fixture(autouse=True)
def _no_recorder_states() -> None:
    """Skip the real recorder query; mapping steps then only see preset/existing values."""
    with patch(
        "custom_components.ev_charging.resolver.async_query_recorder_states",
        new=AsyncMock(return_value=set()),
    ):
        yield


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """The single step creates the config entry with the default global settings."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["data_schema"] is None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {"wallbox_seq": 0, "vehicle_seq": 0, **EXPECTED_HUB_SETTINGS}
    assert result["options"] == {}


async def test_second_entry_is_aborted(hass: HomeAssistant) -> None:
    """A second attempt to set up the integration is rejected."""
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data={})
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


async def _setup_hub(hass: HomeAssistant) -> MockConfigEntry:
    """Create and set up the hub entry with the current data schema."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        data={"wallbox_seq": 0, "vehicle_seq": 0, **EXPECTED_HUB_SETTINGS},
        version=3,
        minor_version=1,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _add_wallbox(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    *,
    expert: dict[str, Any] | None = None,
    roles: dict[str, Any] | None = None,
    plug_state_mapping: list[dict[str, str]] | None = None,
    error_mapping: list[dict[str, str]] | None = None,
    subentry_id: str | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Run the wallbox subentry flow to completion and return the final result."""
    payload = {**WALLBOX_INPUT, **overrides}
    if expert is not None:
        payload["expert"] = {**WALLBOX_INPUT["expert"], **expert}
    else:
        payload["expert"] = dict(WALLBOX_INPUT["expert"])
    if roles is not None:
        payload["roles"] = {**WALLBOX_INPUT["roles"], **roles}
    else:
        payload["roles"] = dict(WALLBOX_INPUT["roles"])

    if subentry_id is not None:
        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_TYPE_WALLBOX),
            context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry_id},
        )
    else:
        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
        )
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], payload)

    if result.get("step_id") == "plug_state_mapping":
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"mapping": plug_state_mapping or []}
        )
    if result.get("step_id") == "error_mapping":
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"mapping": error_mapping or []}
        )
    return result


async def _add_vehicle(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    *,
    cards: list[dict[str, Any]] | None = None,
    roles: dict[str, Any] | None = None,
    charge_state_mapping: list[dict[str, str]] | None = None,
    charge_type_mapping: list[dict[str, str]] | None = None,
    subentry_id: str | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Run the vehicle subentry flow to completion and return the final result."""
    payload = {**VEHICLE_INPUT, **overrides}
    if cards is not None:
        payload["cards"] = cards
    if roles is not None:
        payload["roles"] = {**VEHICLE_INPUT["roles"], **roles}
    else:
        payload["roles"] = dict(VEHICLE_INPUT["roles"])

    if subentry_id is not None:
        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_TYPE_VEHICLE),
            context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry_id},
        )
    else:
        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
        )
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], payload)

    if result.get("step_id") == "charge_state_mapping":
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"mapping": charge_state_mapping or []}
        )
    if result.get("step_id") == "charge_type_mapping":
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"mapping": charge_type_mapping or []}
        )
    return result


async def test_wallbox_can_be_created(hass: HomeAssistant) -> None:
    """The wallbox subentry is created with the first sequential id."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["id"] == "wb001"
    assert result["data"]["name"] == "Carport"
    assert result["data"]["identification_window_s"] == 15
    assert "default_vehicle_id" not in result["data"]
    assert result["data"]["charge_power"]["entity_id"] == "sensor.wallbox_power"
    assert result["data"]["charge_power"]["unit"] == "kW"
    assert result["data"]["plug_state"]["entity_id"] == "sensor.wallbox_plug_state"
    assert result["data"]["error"]["entity_id"] == "binary_sensor.wallbox_error"
    assert result["data"]["error_mapping"] == {}
    subentries = entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)
    assert len(subentries) == 1


async def test_second_wallbox_is_rejected(hass: HomeAssistant) -> None:
    """Only one wallbox instance is allowed."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_wallbox_allowed"


async def test_wallbox_manufacturer_and_model_are_stored(hass: HomeAssistant) -> None:
    """manufacturer and model are optional master data fields."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry, manufacturer="KEBA", model="P40")

    assert result["data"]["manufacturer"] == "KEBA"
    assert result["data"]["model"] == "P40"


async def test_wallbox_start_debounce_out_of_range_is_rejected(hass: HomeAssistant) -> None:
    """start_debounce_s outside 0 to 30 seconds is rejected with an error."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry, expert={"start_debounce_s": 60})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"start_debounce_s": "start_debounce_out_of_range"}


async def test_wallbox_identification_window_out_of_range_is_rejected(
    hass: HomeAssistant,
) -> None:
    """identification_window_s outside 0 to 300 seconds is rejected with an error."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry, expert={"identification_window_s": 400})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"identification_window_s": "identification_window_out_of_range"}


async def test_wallbox_requires_charge_power_and_plug_state(hass: HomeAssistant) -> None:
    """charge_power and plug_state are mandatory roles (5.1)."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(
        hass, entry, roles={"charge_power": None, "plug_state": None, "energy_total": None}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        "charge_power": "charge_power_required",
        "plug_state": "plug_state_required",
        "energy_total": "energy_counter_required",
    }


async def test_wallbox_accepts_energy_session_without_energy_total(hass: HomeAssistant) -> None:
    """Only one of energy_total and energy_session needs to be assigned (5.4)."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(
        hass,
        entry,
        roles={"energy_total": None, "energy_session": "sensor.wallbox_energy_session"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["energy_total"] is None
    assert result["data"]["energy_session"]["entity_id"] == "sensor.wallbox_energy_session"


async def test_plug_state_mapping_is_stored(hass: HomeAssistant) -> None:
    """Submitted plug state mapping rows are stored as a raw-value-to-class dict."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(
        hass,
        entry,
        plug_state_mapping=[
            {"raw_value": "plugged_ev", "class": "connected"},
            {"raw_value": "unplugged", "class": "not_connected"},
        ],
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["plug_state_mapping"] == {
        "plugged_ev": "connected",
        "unplugged": "not_connected",
    }


async def test_binary_sensor_error_role_skips_mapping_step(hass: HomeAssistant) -> None:
    """A binary_sensor error role is read directly, without a mapping step."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
    )
    payload = {**WALLBOX_INPUT, "roles": dict(WALLBOX_INPUT["roles"])}
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], payload)

    assert result["step_id"] == "plug_state_mapping"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping": []}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["error_mapping"] == {}


async def test_state_error_role_requires_mapping_step(hass: HomeAssistant) -> None:
    """A non-binary_sensor error role goes through its own mapping step (E29)."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(
        hass,
        entry,
        roles={"error": "sensor.wallbox_error_state"},
        error_mapping=[{"raw_value": "4", "class": "error"}],
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["error"]["entity_id"] == "sensor.wallbox_error_state"
    assert result["data"]["error_mapping"] == {"4": "error"}


async def test_wallbox_can_be_reconfigured(hass: HomeAssistant) -> None:
    """Renaming the wallbox keeps its id."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)))

    result = await _add_wallbox(hass, entry, subentry_id=subentry.subentry_id, name="Carport neu")

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    updated = entry.subentries[subentry.subentry_id]
    assert updated.data["name"] == "Carport neu"
    assert updated.data["id"] == "wb001"


async def test_wallbox_id_is_never_reused_after_removal(hass: HomeAssistant) -> None:
    """A removed wallbox's id is not handed out to the next one."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)))
    hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)

    result = await _add_wallbox(hass, entry)

    assert result["data"]["id"] == "wb002"


async def test_vehicle_ids_are_sequential_and_never_reused(hass: HomeAssistant) -> None:
    """Vehicles get v001, v002, ... and a removed id is not reused."""
    entry = await _setup_hub(hass)

    first = await _add_vehicle(
        hass,
        entry,
        name="GLB 250+ EQ",
        cards=[{"uid": "ABC123", "label": "Karte GLB", "type": "rfid"}],
    )
    second = await _add_vehicle(
        hass,
        entry,
        name="EQB 250+",
        cards=[{"uid": "DEF456", "label": "Karte EQB", "type": "rfid"}],
    )
    assert first["data"]["id"] == "v001"
    assert second["data"]["id"] == "v002"

    first_subentry_id = next(
        sub.subentry_id
        for sub in entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)
        if sub.data["id"] == "v001"
    )
    hass.config_entries.async_remove_subentry(entry, first_subentry_id)

    third = await _add_vehicle(
        hass,
        entry,
        name="Gast",
        cards=[{"uid": "ABC123", "label": "Karte, neu vergeben", "type": "rfid"}],
    )
    assert third["data"]["id"] == "v003"


async def test_vehicle_requires_capacity_unless_guest(hass: HomeAssistant) -> None:
    """capacity_kwh is mandatory unless the vehicle is a guest vehicle."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )
    no_capacity = {k: v for k, v in VEHICLE_INPUT.items() if k != "capacity_kwh"}
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], no_capacity)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"capacity_kwh": "capacity_required"}

    guest_result = await _add_vehicle(
        hass, entry, name="Gastfahrzeug", is_guest=True, capacity_kwh=None
    )
    assert guest_result["type"] is FlowResultType.CREATE_ENTRY


async def test_cost_mode_is_stored_without_a_follow_up_step(hass: HomeAssistant) -> None:
    """cost_mode is stored as entered; it no longer branches into a cost step."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(hass, entry, cost_mode="static")

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["cost_mode"] == "static"
    assert "static_price" not in result["data"]
    assert "solar_valuation" not in result["data"]


async def test_manufacturer_and_model_are_stored(hass: HomeAssistant) -> None:
    """manufacturer and model are optional master data fields."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(hass, entry, manufacturer="Mercedes-Benz", model="GLB 250+ EQ")

    assert result["data"]["manufacturer"] == "Mercedes-Benz"
    assert result["data"]["model"] == "GLB 250+ EQ"


async def test_duplicate_card_on_active_vehicle_is_rejected(hass: HomeAssistant) -> None:
    """The same card cannot be given to two active vehicles."""
    entry = await _setup_hub(hass)
    await _add_vehicle(
        hass,
        entry,
        name="GLB 250+ EQ",
        cards=[{"uid": "ABC123", "label": "Karte GLB", "type": "rfid"}],
    )

    result = await _add_vehicle(
        hass,
        entry,
        name="Zweitwagen",
        cards=[{"uid": "ABC123", "label": "Karte Zweitwagen", "type": "rfid"}],
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"cards": "duplicate_card"}


async def test_duplicate_card_within_the_same_submission_is_rejected(hass: HomeAssistant) -> None:
    """A vehicle cannot be given the same card identifier twice."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(
        hass,
        entry,
        cards=[
            {"uid": "ABC123", "label": "Karte 1", "type": "rfid"},
            {"uid": "abc-123", "label": "Karte 2", "type": "rfid"},
        ],
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"cards": "duplicate_card"}


async def test_active_vehicle_requires_at_least_one_identification(hass: HomeAssistant) -> None:
    """A vehicle cannot be saved as active without a card or identify_by_vehicle_api."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(hass, entry, cards=[])

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"cards": "identification_required"}


@pytest.mark.parametrize("raw_uid", ["0", "unknown", "UNAVAILABLE", "", "  "])
async def test_invalid_card_uid_values_are_rejected(hass: HomeAssistant, raw_uid: str) -> None:
    """Values that never count as a real identification are rejected."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(
        hass, entry, cards=[{"uid": raw_uid, "label": "Karte", "type": "rfid"}]
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"cards": "invalid_card_uid"}


async def test_card_type_is_stored(hass: HomeAssistant) -> None:
    """The card's type (rfid or emaid) is stored as selected."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(
        hass, entry, cards=[{"uid": "DEABCC123456789", "label": "eMAID", "type": "emaid"}]
    )

    assert result["data"]["cards"][0]["type"] == "emaid"


async def test_card_type_selector_uses_fixed_labels(hass: HomeAssistant) -> None:
    """The card type selector uses fixed RFID/EMAID labels (translation_key does not
    resolve inside this ObjectSelector field)."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )
    schema = result["data_schema"].schema
    cards_key = next(key for key in schema if str(key) == "cards")
    type_selector = schema[cards_key].config["fields"]["type"]["selector"]
    options = type_selector.config["options"]

    assert {"value": "rfid", "label": "RFID"} in options
    assert {"value": "emaid", "label": "EMAID"} in options


async def test_card_on_an_inactive_vehicle_is_dropped(hass: HomeAssistant) -> None:
    """Cards submitted for a vehicle created inactive are not stored."""
    entry = await _setup_hub(hass)
    await _add_vehicle(
        hass,
        entry,
        name="GLB 250+ EQ",
        cards=[{"uid": "ABC123", "label": "Karte GLB", "type": "rfid"}],
    )

    result = await _add_vehicle(
        hass,
        entry,
        name="EQB 250+",
        active=False,
        cards=[{"uid": "ABC123", "label": "Karte EQB", "type": "rfid"}],
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["cards"] == []


async def test_card_uid_is_normalized(hass: HomeAssistant) -> None:
    """A card uid is normalized to upper case without separators when stored."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(
        hass,
        entry,
        name="GLB 250+ EQ",
        cards=[{"uid": "de-abc-c12345678-9", "label": "eMAID", "type": "emaid"}],
    )

    assert result["data"]["cards"][0]["uid"] == "DEABCC123456789"


async def test_vehicle_can_be_renamed_and_deactivated(hass: HomeAssistant) -> None:
    """Reconfiguring a vehicle can rename it, flip active off, and clears its cards."""
    entry = await _setup_hub(hass)
    await _add_vehicle(hass, entry, name="GLB 250+ EQ")
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)))

    result = await _add_vehicle(
        hass, entry, subentry_id=subentry.subentry_id, name="EQB 250+", active=False
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    updated = entry.subentries[subentry.subentry_id]
    assert updated.data["name"] == "EQB 250+"
    assert updated.data["active"] is False
    assert updated.data["id"] == "v001"
    assert updated.data["cards"] == []


async def test_reactivating_a_vehicle_requires_a_new_card(hass: HomeAssistant) -> None:
    """A vehicle set inactive loses its cards and needs a new one to be reactivated."""
    entry = await _setup_hub(hass)
    await _add_vehicle(hass, entry, name="GLB 250+ EQ")
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)))

    result = await _add_vehicle(hass, entry, subentry_id=subentry.subentry_id, active=False)
    assert result["type"] is FlowResultType.ABORT
    assert entry.subentries[subentry.subentry_id].data["cards"] == []

    result = await _add_vehicle(
        hass, entry, subentry_id=subentry.subentry_id, active=True, cards=[]
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"cards": "identification_required"}

    result = await _add_vehicle(hass, entry, subentry_id=subentry.subentry_id, active=True)

    assert result["type"] is FlowResultType.ABORT
    assert entry.subentries[subentry.subentry_id].data["cards"][0]["uid"] == "ABC123"


async def test_vehicle_can_be_removed(hass: HomeAssistant) -> None:
    """A vehicle subentry can be removed."""
    entry = await _setup_hub(hass)
    await _add_vehicle(hass, entry, name="Gastfahrzeug", is_guest=True, capacity_kwh=None)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)))

    assert hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)

    assert entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE) == []


async def test_identify_by_vehicle_api_requires_charge_state_and_location(
    hass: HomeAssistant,
) -> None:
    """identify_by_vehicle_api needs charge_state and location assigned (4.4)."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(hass, entry, identify_by_vehicle_api=True)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"identify_by_vehicle_api": "identify_by_vehicle_api_requires_roles"}


async def test_identify_by_vehicle_api_allowed_with_required_roles(hass: HomeAssistant) -> None:
    """A vehicle without cards can rely solely on identify_by_vehicle_api."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(
        hass,
        entry,
        cards=[],
        identify_by_vehicle_api=True,
        roles={
            "charge_state": "sensor.vehicle_charge_state",
            "location": "device_tracker.vehicle",
        },
        charge_state_mapping=[{"raw_value": "0", "class": "charging"}],
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["identify_by_vehicle_api"] is True
    assert result["data"]["cards"] == []


async def test_charge_state_and_charge_type_mapping_are_stored(hass: HomeAssistant) -> None:
    """Vehicle charge_state and charge_type roles each get their own mapping."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(
        hass,
        entry,
        roles={
            "charge_state": "sensor.vehicle_charge_state",
            "charge_type": "sensor.vehicle_charge_type",
        },
        charge_state_mapping=[{"raw_value": "0", "class": "charging"}],
        charge_type_mapping=[{"raw_value": "13", "class": "ac"}],
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["charge_state_mapping"] == {"0": "charging"}
    assert result["data"]["charge_type_mapping"] == {"13": "ac"}


async def test_preset_covering_role_skips_mapping_step(hass: HomeAssistant) -> None:
    """A role backed by an entity from a matched, fully covering preset needs no
    manual mapping step at all."""
    registry = er.async_get(hass)
    charge_state_entry = registry.async_get_or_create(
        "sensor", "mercedes_me", "vehicle_charge_state_unique"
    )
    hass.states.async_set(charge_state_entry.entity_id, "0")

    entry = await _setup_hub(hass)
    result = await _add_vehicle(hass, entry, roles={"charge_state": charge_state_entry.entity_id})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    # The full preset is stored, not just the code observed just now, so any
    # code that arrives later is already classified.
    assert result["data"]["charge_state_mapping"]["0"] == "charging"
    assert len(result["data"]["charge_state_mapping"]) == 17


async def test_identification_hint_shows_current_wallbox_value(hass: HomeAssistant) -> None:
    """The vehicle dialog shows the wallbox's current identification value."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry, roles={"identification": "sensor.wallbox_identification"})
    hass.states.async_set("sensor.wallbox_identification", "BAEB2194")

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )

    assert result["description_placeholders"]["identification_hint"] == "BAEB2194"


async def test_identification_hint_is_blank_without_a_readable_value(
    hass: HomeAssistant,
) -> None:
    """The hint stays blank when no wallbox exists or its value is not usable."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )

    assert result["description_placeholders"]["identification_hint"] == "-"


async def test_reconfigure_updates_global_settings(hass: HomeAssistant) -> None:
    """The hub's global settings can be edited after setup."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "update_interval_s": 60,
            "solar_valuation": "zero",
            "geocoding_enabled": True,
            "geocoding_url": "https://example.invalid/reverse",
            "geocoding_contact": "test@example.invalid",
            "estimate_uncertain_threshold_pct": 10,
            "grid_power_inverted": False,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["update_interval_s"] == 60
    assert entry.data["solar_valuation"] == "zero"
    assert entry.data["geocoding_contact"] == "test@example.invalid"
    assert entry.data["estimate_uncertain_threshold_pct"] == 10
    # Sequence counters are untouched by the settings reconfigure.
    assert entry.data["wallbox_seq"] == 0


async def test_reconfigure_stores_grid_and_price_roles(hass: HomeAssistant) -> None:
    """Grid balance and price roles are editable from the hub's global settings (4.2, E24)."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "update_interval_s": 30,
            "solar_valuation": "feed_in_tariff",
            "geocoding_enabled": False,
            "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
            "estimate_uncertain_threshold_pct": 5,
            "grid_power": "sensor.grid_power",
            "grid_power_inverted": True,
            "price_feed_in_fixed": 0.08,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert entry.data["grid_power"]["entity_id"] == "sensor.grid_power"
    assert entry.data["grid_power_inverted"] is True
    assert entry.data["price_feed_in_fixed"] == 0.08


async def test_reconfigure_rejects_grid_power_and_grid_import_together(
    hass: HomeAssistant,
) -> None:
    """grid_power and grid_import/grid_export are mutually exclusive alternatives (4.2)."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "update_interval_s": 30,
            "solar_valuation": "feed_in_tariff",
            "geocoding_enabled": False,
            "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
            "estimate_uncertain_threshold_pct": 5,
            "grid_power": "sensor.grid_power",
            "grid_power_inverted": False,
            "grid_import": "sensor.grid_power",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"grid_power": "grid_source_conflict"}


async def test_reconfigure_rejects_price_entity_and_fixed_value_together(
    hass: HomeAssistant,
) -> None:
    """price_grid accepts an entity role or a fixed value, never both (4.2)."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "update_interval_s": 30,
            "solar_valuation": "feed_in_tariff",
            "geocoding_enabled": False,
            "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
            "estimate_uncertain_threshold_pct": 5,
            "grid_power_inverted": False,
            "price_grid": "sensor.grid_power",
            "price_grid_fixed": 0.30,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"price_grid": "price_source_conflict"}


async def test_reconfigure_requires_a_contact_when_geocoding_is_enabled(
    hass: HomeAssistant,
) -> None:
    """Geocoding cannot be enabled without a contact for the User-Agent."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "update_interval_s": 30,
            "solar_valuation": "feed_in_tariff",
            "geocoding_enabled": True,
            "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
            "estimate_uncertain_threshold_pct": 5,
            "grid_power_inverted": False,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"geocoding_contact": "geocoding_contact_required"}


async def test_reconfigure_rejects_update_interval_out_of_range(hass: HomeAssistant) -> None:
    """update_interval_s outside 15 to 300 seconds is rejected with an error."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "update_interval_s": 10,
            "solar_valuation": "feed_in_tariff",
            "geocoding_enabled": False,
            "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
            "estimate_uncertain_threshold_pct": 5,
            "grid_power_inverted": False,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"update_interval_s": "update_interval_out_of_range"}


async def test_renaming_role_entity_keeps_resolution_valid(hass: HomeAssistant) -> None:
    """Renaming a role's underlying entity does not break resolution (E15, 4.8)."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get_or_create("sensor", "test", "wallbox_power_unique")
    hass.states.async_set(entity_entry.entity_id, "1.5", {"unit_of_measurement": "kW"})

    entry = await _setup_hub(hass)
    result = await _add_wallbox(hass, entry, roles={"charge_power": entity_entry.entity_id})
    registry_entry_id = result["data"]["charge_power"]["registry_entry_id"]
    assert registry_entry_id == entity_entry.id

    registry.async_update_entity(entity_entry.entity_id, new_entity_id="sensor.renamed_power")
    await hass.async_block_till_done()

    from custom_components.ev_charging import resolver
    from custom_components.ev_charging.models import EntityRole

    role = EntityRole(
        entity_id=entity_entry.entity_id, registry_entry_id=registry_entry_id, unit="kW"
    )
    assert resolver.resolve_entity_id(hass, role) == "sensor.renamed_power"
