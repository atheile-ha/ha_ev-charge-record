"""Tests for the ev_charging config flow."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from custom_components.ev_charging.const import (
    DOMAIN,
    NO_VEHICLE_INTEGRATION,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
)
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    MockModule,
    mock_integration,
)

from tests.fake_modbus import NO_CONNECTION, FakeDevice, install

WALLBOX_MAPPING_ID = "openems_keba_p40"
VEHICLE_MAPPING_ID = "mbapi2020_mercedes_me"

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
async def _unload_entries(hass: HomeAssistant) -> AsyncGenerator[None]:
    """Let reloads scheduled by the flows finish, then unload what is still loaded."""
    yield
    await hass.async_block_till_done()
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture(autouse=True)
def _no_device(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep every wallbox set up in these tests from reaching a real device."""
    install(monkeypatch, FakeDevice([(NO_CONNECTION,)]))


@pytest.fixture(autouse=True)
def _mock_source_integrations(hass: HomeAssistant) -> None:
    """Make the mapped source integrations appear installed and current enough (4.7, O20)."""
    mock_integration(hass, MockModule("openems", partial_manifest={"version": "1.7.2"}))
    mock_integration(hass, MockModule("mbapi2020", partial_manifest={"version": "0.29.2"}))
    mock_integration(hass, MockModule("myskoda", partial_manifest={"version": "1.36.1"}))


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
    mapping_id: str | None = WALLBOX_MAPPING_ID,
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
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping_id": mapping_id}
    )
    if result.get("step_id") in ("details", "details_reconfigure"):
        result = await hass.config_entries.subentries.async_configure(result["flow_id"], payload)
    return result


async def _add_vehicle(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    *,
    cards: list[dict[str, Any]] | None = None,
    roles: dict[str, Any] | None = None,
    mapping_id: str | None = None,
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
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping_id": mapping_id or NO_VEHICLE_INTEGRATION}
    )
    if result.get("step_id") in ("details", "details_reconfigure"):
        result = await hass.config_entries.subentries.async_configure(result["flow_id"], payload)
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
    assert result["data"]["mapping_id"] == WALLBOX_MAPPING_ID
    subentries = entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)
    assert len(subentries) == 1


def _mapping_id_options(data_schema: Any) -> set[str]:
    """Return the selectable values of a device-choice form's mapping_id field."""
    schema = data_schema.schema
    key = next(key for key in schema if str(key) == "mapping_id")
    selector = schema[key]
    # vol.Any(None, SelectSelector(...)) for the vehicle flow: unwrap to the selector.
    if hasattr(selector, "validators"):
        selector = next(v for v in selector.validators if hasattr(v, "config"))
    return {option["value"] for option in selector.config["options"]}


def _excluded_texts(data_schema: Any) -> list[str]:
    """Return the texts shown in a device-choice form's collapsed excluded-devices section."""
    schema = data_schema.schema
    key = next((key for key in schema if str(key) == "excluded"), None)
    if key is None:
        return []
    inner_schema = schema[key].schema.schema
    return [selector.config["label"] for selector in inner_schema.values()]


async def test_wallbox_device_step_is_shown_first(hass: HomeAssistant) -> None:
    """The wallbox flow's first step is the mandatory device choice (O19)."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert WALLBOX_MAPPING_ID in _mapping_id_options(result["data_schema"])


async def test_wallbox_device_choice_excludes_devices_below_min_version(
    hass: HomeAssistant,
) -> None:
    """A device whose source integration is too old is not offered, with a hint (4.7, O20)."""
    mock_integration(hass, MockModule("openems", partial_manifest={"version": "1.0.0"}))
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
    )

    assert WALLBOX_MAPPING_ID not in _mapping_id_options(result["data_schema"])
    assert any("KEBA" in text for text in _excluded_texts(result["data_schema"]))


async def test_wallbox_device_choice_has_no_excluded_section_when_nothing_is_excluded(
    hass: HomeAssistant,
) -> None:
    """No collapsed section appears when every mapped device's source is available."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
    )

    assert _excluded_texts(result["data_schema"]) == []


async def test_vehicle_device_choice_excluded_text_is_translated(hass: HomeAssistant) -> None:
    """The excluded-devices text comes from translations, not a hardcoded language (4.7)."""
    hass.config.language = "de"
    mock_integration(hass, MockModule("mbapi2020", partial_manifest={"version": "0.1.0"}))
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )

    texts = _excluded_texts(result["data_schema"])
    assert any(
        "Mercedes me connect" in text and "Quellintegration älter als" in text for text in texts
    )


async def test_wallbox_reconfigure_keeps_the_current_device_even_if_now_too_old(
    hass: HomeAssistant,
) -> None:
    """Reconfiguring never silently drops the subentry's already-chosen device (O20)."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)))
    mock_integration(hass, MockModule("openems", partial_manifest={"version": "1.0.0"}))

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )

    assert WALLBOX_MAPPING_ID in _mapping_id_options(result["data_schema"])


async def test_wallbox_device_can_be_changed_freely(hass: HomeAssistant) -> None:
    """The chosen device can be changed on an existing wallbox at any time."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)))

    result = await _add_wallbox(
        hass, entry, subentry_id=subentry.subentry_id, mapping_id="openems_webasto_next"
    )

    assert result["type"] is FlowResultType.ABORT
    assert entry.subentries[subentry.subentry_id].data["mapping_id"] == "openems_webasto_next"


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


async def test_wallbox_device_choice_leaves_no_mapping_step(hass: HomeAssistant) -> None:
    """After the device is chosen, submitting the details form finishes the flow directly."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping_id": WALLBOX_MAPPING_ID}
    )
    assert result["step_id"] == "details"

    payload = {**WALLBOX_INPUT, "roles": dict(WALLBOX_INPUT["roles"])}
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], payload)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["mapping_id"] == WALLBOX_MAPPING_ID


async def test_state_error_role_is_stored_without_a_mapping_step(hass: HomeAssistant) -> None:
    """A non-binary_sensor error role is stored directly; its classification comes from the
    device's mapping file, not from a step in this flow (E29)."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry, roles={"error": "sensor.wallbox_error_state"})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["error"]["entity_id"] == "sensor.wallbox_error_state"


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
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping_id": NO_VEHICLE_INTEGRATION}
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
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping_id": NO_VEHICLE_INTEGRATION}
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
        mapping_id=VEHICLE_MAPPING_ID,
        roles={
            "charge_state": "sensor.vehicle_charge_state",
            "location": "device_tracker.vehicle",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["identify_by_vehicle_api"] is True
    assert result["data"]["cards"] == []


async def test_vehicle_device_choice_is_optional_without_charge_roles(
    hass: HomeAssistant,
) -> None:
    """A vehicle without charge_state or charge_type needs no device (5.2), e.g. a guest
    vehicle or one tracked only via soc/odometer/location."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(hass, entry, mapping_id=None)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["mapping_id"] is None


async def test_vehicle_charge_state_without_a_device_is_rejected(hass: HomeAssistant) -> None:
    """Assigning charge_state without choosing a device is an incomplete configuration (E33)."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(
        hass,
        entry,
        mapping_id=None,
        roles={"charge_state": "sensor.vehicle_charge_state"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "charge_state_requires_mapping"}


async def test_vehicle_charge_state_and_charge_type_with_a_device_are_stored(
    hass: HomeAssistant,
) -> None:
    """Vehicle charge_state and charge_type roles are stored together with the chosen device."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(
        hass,
        entry,
        mapping_id=VEHICLE_MAPPING_ID,
        roles={
            "charge_state": "sensor.vehicle_charge_state",
            "charge_type": "sensor.vehicle_charge_type",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["mapping_id"] == VEHICLE_MAPPING_ID
    assert result["data"]["charge_state"]["entity_id"] == "sensor.vehicle_charge_state"
    assert result["data"]["charge_type"]["entity_id"] == "sensor.vehicle_charge_type"


async def test_identification_hint_shows_current_wallbox_value(hass: HomeAssistant) -> None:
    """The vehicle dialog shows the wallbox's current identification value."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry, roles={"identification": "sensor.wallbox_identification"})
    hass.states.async_set("sensor.wallbox_identification", "BAEB2194")

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping_id": NO_VEHICLE_INTEGRATION}
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
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping_id": NO_VEHICLE_INTEGRATION}
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


# ------------------------------------------------------------------ direct read

DEVICE_HOST = "192.0.2.10"

REGISTER = {"identification_from_register": True}
DIRECT_READ = {
    "host": DEVICE_HOST,
    "port": 502,
    "unit_id": 255,
}


def _section_fields(data_schema: Any, section_name: str) -> set[str]:
    """Return the field names of one section of a details form."""
    schema = data_schema.schema
    key = next(key for key in schema if str(key) == section_name)
    return {str(field) for field in schema[key].schema.schema}


async def _details_form(hass: HomeAssistant, entry: MockConfigEntry, mapping_id: str) -> Any:
    """Open the wallbox details form for a chosen device."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping_id": mapping_id}
    )
    assert result["step_id"] == "details"
    return result


async def test_the_register_is_not_read_by_default(hass: HomeAssistant) -> None:
    """A wallbox saved without touching the options does not read the device."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert "direct_read_enabled" not in result["data"]
    assert result["data"]["host"] is None
    assert result["data"]["port"] == 502
    assert result["data"]["unit_id"] == 255
    assert result["data"]["identification_from_register"] is False


async def test_the_direct_read_settings_are_expert_options(hass: HomeAssistant) -> None:
    """Address, port and unit id sit in the expert options, without a switch of their own."""
    entry = await _setup_hub(hass)

    result = await _details_form(hass, entry, WALLBOX_MAPPING_ID)

    fields = _section_fields(result["data_schema"], "expert")
    assert {"host", "port", "unit_id"} <= fields
    assert "direct_read_enabled" not in fields
    assert result["step_id"] == "details"


async def test_the_direct_read_can_be_set_up_with_the_register_as_the_identification(
    hass: HomeAssistant,
) -> None:
    """The register is chosen as the source of the identification, next to the entity option."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(
        hass,
        entry,
        roles=REGISTER,
        expert=DIRECT_READ,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert "direct_read_enabled" not in result["data"]
    assert result["data"]["host"] == DEVICE_HOST
    assert result["data"]["port"] == 502
    assert result["data"]["unit_id"] == 255
    assert result["data"]["identification_from_register"] is True
    assert result["data"]["identification"] is None


async def test_the_register_is_offered_only_for_a_device_that_has_one(hass: HomeAssistant) -> None:
    """The KEBA P40 has a register for the identification; the Webasto Next has none."""
    entry = await _setup_hub(hass)

    keba = await _details_form(hass, entry, WALLBOX_MAPPING_ID)
    assert "identification_from_register" in _section_fields(keba["data_schema"], "roles")
    hass.config_entries.subentries.async_abort(keba["flow_id"])

    webasto = await _details_form(hass, entry, "openems_webasto_next")
    assert "identification_from_register" not in _section_fields(webasto["data_schema"], "roles")


async def test_host_port_and_unit_id_are_not_asked_while_the_register_is_not_used(
    hass: HomeAssistant,
) -> None:
    """Nothing about the connection is checked while the identification is not read from it."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry, expert={"host": "", "port": 70000, "unit_id": 999})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] is None


async def test_the_direct_read_needs_an_address(hass: HomeAssistant) -> None:
    """With the register as the source of the identification, an address is required."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry, roles=REGISTER, expert={**DIRECT_READ, "host": "  "})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"host": "host_required"}


@pytest.mark.parametrize("port", [0, 65536])
async def test_the_direct_read_port_must_be_valid(hass: HomeAssistant, port: int) -> None:
    """The port is from 1 to 65535."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry, roles=REGISTER, expert={**DIRECT_READ, "port": port})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"port": "port_out_of_range"}


@pytest.mark.parametrize("unit_id", [-1, 256])
async def test_the_direct_read_unit_id_must_be_valid(hass: HomeAssistant, unit_id: int) -> None:
    """The unit id is from 0 to 255."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(
        hass, entry, roles=REGISTER, expert={**DIRECT_READ, "unit_id": unit_id}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"unit_id": "unit_id_out_of_range"}


async def test_the_unit_id_zero_and_the_port_limits_are_accepted(hass: HomeAssistant) -> None:
    """The bounds themselves are valid."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(
        hass, entry, roles=REGISTER, expert={**DIRECT_READ, "port": 65535, "unit_id": 0}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["port"] == 65535
    assert result["data"]["unit_id"] == 0


async def test_the_identification_is_an_entity_or_the_register_not_both(
    hass: HomeAssistant,
) -> None:
    """An identification entity and the register together are rejected."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(
        hass,
        entry,
        roles={
            "identification": "sensor.wallbox_identification",
            "identification_from_register": True,
        },
        expert=DIRECT_READ,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"identification": "identification_source_conflict"}


async def test_the_direct_read_settings_can_be_changed_without_a_new_wallbox(
    hass: HomeAssistant,
) -> None:
    """A new address is a change of the expert options; the wallbox keeps its id."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry, roles=REGISTER, expert=DIRECT_READ)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)))

    result = await _add_wallbox(
        hass,
        entry,
        subentry_id=subentry.subentry_id,
        roles=REGISTER,
        expert={**DIRECT_READ, "host": "192.0.2.11", "port": 1502, "unit_id": 1},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    data = entry.subentries[subentry.subentry_id].data
    assert data["id"] == "wb001"
    assert data["host"] == "192.0.2.11"
    assert data["port"] == 1502
    assert data["unit_id"] == 1
    assert data["identification_from_register"] is True

    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_changing_to_a_device_without_a_register_drops_the_register_choice(
    hass: HomeAssistant,
) -> None:
    """The register option is not offered for the new device, so the choice does not carry over."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry, roles=REGISTER, expert=DIRECT_READ)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)))

    result = await _add_wallbox(
        hass,
        entry,
        subentry_id=subentry.subentry_id,
        mapping_id="openems_webasto_next",
    )

    assert result["type"] is FlowResultType.ABORT
    data = entry.subentries[subentry.subentry_id].data
    assert data["identification_from_register"] is False

    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_the_reconfigure_form_suggests_the_stored_entities(hass: HomeAssistant) -> None:
    """The stored entities are offered as suggested values, empty roles as none."""
    entry = await _setup_hub(hass)
    await _add_vehicle(
        hass, entry, roles={"soc": "sensor.glb_soc", "charge_power": "sensor.glb_power"}
    )
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)))

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"mapping_id": NO_VEHICLE_INTEGRATION}
    )

    assert result["step_id"] == "details_reconfigure"
    roles = next(value for key, value in result["data_schema"].schema.items() if key == "roles")
    suggested = {
        str(marker): (marker.description or {}).get("suggested_value")
        for marker in roles.schema.schema
    }
    assert suggested["soc"] == "sensor.glb_soc"
    assert suggested["charge_power"] == "sensor.glb_power"
    assert suggested["range"] is None


async def test_an_entity_role_can_be_cleared_in_the_reconfigure_form(hass: HomeAssistant) -> None:
    """A role left out of the submitted form is removed, not restored from the stored value."""
    entry = await _setup_hub(hass)
    await _add_vehicle(hass, entry, roles={"soc": "sensor.glb_soc"})
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)))

    result = await _add_vehicle(hass, entry, subentry_id=subentry.subentry_id, roles={})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry.subentry_id].data["soc"] is None
