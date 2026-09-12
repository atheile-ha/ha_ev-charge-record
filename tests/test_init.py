"""Tests for setting up, unloading and removing the ev_charging config entry."""

from custom_components.ev_charging.const import DOMAIN, TITLE
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """The config entry loads and unloads again."""
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_remove_entry(hass: HomeAssistant) -> None:
    """Removing the config entry leaves nothing behind."""
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_remove(entry.entry_id) == {"require_restart": False}
    await hass.async_block_till_done()

    assert hass.config_entries.async_entries(DOMAIN) == []
    assert DOMAIN not in hass.data


async def test_setup_creates_no_entities(hass: HomeAssistant) -> None:
    """This stage has no platforms, so no entities appear."""
    entry = MockConfigEntry(domain=DOMAIN, title=TITLE, data={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert [state.entity_id for state in hass.states.async_all()] == []
