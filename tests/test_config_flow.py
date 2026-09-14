"""Tests for the ev_charging config flow."""

from typing import Any

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
from pytest_homeassistant_custom_component.common import MockConfigEntry

WALLBOX_INPUT: dict[str, Any] = {
    "name": "Carport",
    "current_type": "ac",
    "max_power_kw": 11.0,
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
}

EXPECTED_HUB_SETTINGS: dict[str, Any] = {
    "update_interval_s": 30,
    "solar_valuation": "feed_in_tariff",
    "geocoding_enabled": True,
    "geocoding_url": "https://nominatim.openstreetmap.org/reverse",
    "geocoding_contact": None,
    "estimate_uncertain_threshold_pct": 5,
}


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
        version=2,
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
    **overrides: Any,
) -> dict[str, Any]:
    """Run the wallbox subentry flow to completion and return the final result."""
    payload = {**WALLBOX_INPUT, **overrides}
    if expert is not None:
        payload["expert"] = {**WALLBOX_INPUT["expert"], **expert}
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
    )
    return await hass.config_entries.subentries.async_configure(result["flow_id"], payload)


async def _add_vehicle(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    *,
    cards: list[dict[str, Any]] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Run the vehicle subentry flow to completion and return the final result."""
    payload = {**VEHICLE_INPUT, **overrides}
    if cards is not None:
        payload["cards"] = cards
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )
    return await hass.config_entries.subentries.async_configure(result["flow_id"], payload)


async def test_wallbox_can_be_created(hass: HomeAssistant) -> None:
    """The wallbox subentry is created with the first sequential id."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["id"] == "wb001"
    assert result["data"]["name"] == "Carport"
    assert result["data"]["identification_window_s"] == 15
    assert "default_vehicle_id" not in result["data"]
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


async def test_wallbox_can_be_reconfigured(hass: HomeAssistant) -> None:
    """Renaming the wallbox keeps its id."""
    entry = await _setup_hub(hass)
    await _add_wallbox(hass, entry)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)))

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**WALLBOX_INPUT, "name": "Carport neu"}
    )

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


async def test_active_vehicle_requires_at_least_one_card(hass: HomeAssistant) -> None:
    """A vehicle cannot be saved as active without at least one card."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(hass, entry, cards=[])

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"cards": "card_required"}


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

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**VEHICLE_INPUT, "name": "EQB 250+", "active": False}
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

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**VEHICLE_INPUT, "active": False}
    )
    assert result["type"] is FlowResultType.ABORT
    assert entry.subentries[subentry.subentry_id].data["cards"] == []

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**VEHICLE_INPUT, "active": True, "cards": []}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"cards": "card_required"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**VEHICLE_INPUT, "active": True}
    )

    assert result["type"] is FlowResultType.ABORT
    assert entry.subentries[subentry.subentry_id].data["cards"][0]["uid"] == "ABC123"


async def test_vehicle_can_be_removed(hass: HomeAssistant) -> None:
    """A vehicle subentry can be removed."""
    entry = await _setup_hub(hass)
    await _add_vehicle(hass, entry, name="Gastfahrzeug", is_guest=True, capacity_kwh=None)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)))

    assert hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)

    assert entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE) == []


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
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"update_interval_s": "update_interval_out_of_range"}
