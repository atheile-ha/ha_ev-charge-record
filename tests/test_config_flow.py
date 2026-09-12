"""Tests for the ev_charging config flow."""

from typing import Any

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
    "session_strategy": "plug_state",
    "power_threshold_kw": 0.5,
    "start_debounce_s": 20,
    "min_pause_min": 15,
    "session_end_pause_min": 240,
    "final_values_grace_min": 30,
    "identification_max_age_min": 5,
    "error_debounce_s": 30,
    "session_stale_h": 12,
}

VEHICLE_INPUT: dict[str, Any] = {
    "name": "GLB 250+ EQ",
    "active": True,
    "is_guest": False,
    "capacity_kwh": 85.0,
    "solar_valuation": "feed_in_tariff",
}


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """The single step creates the config entry without any input."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["data_schema"] is None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {"wallbox_seq": 0, "vehicle_seq": 0}
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
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data={"wallbox_seq": 0, "vehicle_seq": 0})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _add_wallbox(
    hass: HomeAssistant, entry: MockConfigEntry, **overrides: Any
) -> dict[str, Any]:
    """Run the wallbox subentry flow to completion and return the final result."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_WALLBOX), context={"source": SOURCE_USER}
    )
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**WALLBOX_INPUT, **overrides}
    )


async def _add_vehicle(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    *,
    cards: tuple[dict[str, Any], ...] = (),
    **overrides: Any,
) -> dict[str, Any]:
    """Run the vehicle subentry flow to completion and return the final result."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**VEHICLE_INPUT, **overrides}
    )
    for card in cards:
        assert result["type"] is FlowResultType.MENU
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"next_step_id": "add_card"}
        )
        result = await hass.config_entries.subentries.async_configure(result["flow_id"], card)
    assert result["type"] is FlowResultType.MENU
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "finish"}
    )


async def test_wallbox_can_be_created(hass: HomeAssistant) -> None:
    """The wallbox subentry is created with the first sequential id."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["id"] == "wb001"
    assert result["data"]["name"] == "Carport"
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


async def test_wallbox_start_debounce_out_of_range_is_rejected(hass: HomeAssistant) -> None:
    """start_debounce_s outside 5 to 120 seconds is rejected with an error."""
    entry = await _setup_hub(hass)

    result = await _add_wallbox(hass, entry, start_debounce_s=200)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"start_debounce_s": "start_debounce_out_of_range"}


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

    first = await _add_vehicle(hass, entry, name="GLB 250+ EQ")
    second = await _add_vehicle(hass, entry, name="EQB 250+")
    assert first["data"]["id"] == "v001"
    assert second["data"]["id"] == "v002"

    first_subentry_id = next(
        sub.subentry_id
        for sub in entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)
        if sub.data["id"] == "v001"
    )
    hass.config_entries.async_remove_subentry(entry, first_subentry_id)

    third = await _add_vehicle(hass, entry, name="Gast")
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


async def test_vehicle_fixed_valuation_requires_value(hass: HomeAssistant) -> None:
    """solar_valuation_fixed is mandatory when solar_valuation is 'fixed'."""
    entry = await _setup_hub(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**VEHICLE_INPUT, "solar_valuation": "fixed"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"solar_valuation_fixed": "fixed_valuation_required"}


async def test_duplicate_card_on_active_vehicle_is_rejected(hass: HomeAssistant) -> None:
    """The same card cannot be given to two active vehicles."""
    entry = await _setup_hub(hass)
    await _add_vehicle(
        hass, entry, name="GLB 250+ EQ", cards=[{"uid": "ABC123", "label": "Karte GLB"}]
    )

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_VEHICLE), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**VEHICLE_INPUT, "name": "Zweitwagen"}
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "add_card"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"uid": "ABC123", "label": "Karte Zweitwagen"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_card"
    assert result["errors"] == {"uid": "duplicate_card"}


async def test_duplicate_card_on_inactive_vehicle_is_allowed(hass: HomeAssistant) -> None:
    """Reusing a card already held by an active vehicle is allowed on an inactive one."""
    entry = await _setup_hub(hass)
    await _add_vehicle(
        hass, entry, name="GLB 250+ EQ", cards=[{"uid": "ABC123", "label": "Karte GLB"}]
    )

    result = await _add_vehicle(
        hass,
        entry,
        name="EQB 250+",
        active=False,
        cards=[{"uid": "ABC123", "label": "Karte EQB, historisch"}],
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["cards"][0]["uid"] == "ABC123"


async def test_card_uid_is_normalized(hass: HomeAssistant) -> None:
    """A card uid is normalized to upper case without separators when stored."""
    entry = await _setup_hub(hass)

    result = await _add_vehicle(
        hass,
        entry,
        name="GLB 250+ EQ",
        cards=[{"uid": "de-abc-c12345678-9", "label": "eMAID"}],
    )

    assert result["data"]["cards"][0]["uid"] == "DEABCC123456789"


async def test_vehicle_can_be_renamed_and_deactivated(hass: HomeAssistant) -> None:
    """Reconfiguring a vehicle can rename it and flip active off."""
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
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "finish"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    updated = entry.subentries[subentry.subentry_id]
    assert updated.data["name"] == "EQB 250+"
    assert updated.data["active"] is False
    assert updated.data["id"] == "v001"


async def test_vehicle_can_be_removed(hass: HomeAssistant) -> None:
    """A vehicle subentry can be removed."""
    entry = await _setup_hub(hass)
    await _add_vehicle(hass, entry, name="Gastfahrzeug", is_guest=True, capacity_kwh=None)
    subentry = next(iter(entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)))

    assert hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)

    assert entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE) == []
