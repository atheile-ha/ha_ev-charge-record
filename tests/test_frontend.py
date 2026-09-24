"""Tests for serving the bundle and registering the panel and the dashboard cards."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from custom_components.ev_charging import _bundle_digest
from custom_components.ev_charging.const import (
    DOMAIN,
    FRONTEND_BUNDLE_FILENAME,
    FRONTEND_STATIC_URL_PATH,
    PANEL_URL_PATH,
    PANEL_WEBCOMPONENT,
    TITLE,
)
from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.translation import async_get_translations
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

COMPONENT = Path(__file__).parent.parent / "custom_components" / "ev_charging"
FRONTEND_DIR = COMPONENT / "frontend"
FRONTEND_SOURCES = COMPONENT.parent.parent / "frontend" / "src"


def _bundle_url(hass: HomeAssistant, version: str) -> str:
    digest = hashlib.sha256((FRONTEND_DIR / FRONTEND_BUNDLE_FILENAME).read_bytes()).hexdigest()
    start = hass.data[DOMAIN]["frontend_start_token"]
    return f"{FRONTEND_STATIC_URL_PATH}?v={version}&h={digest[:12]}&s={start}"


def _manifest_version() -> str:
    return json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))["version"]


@pytest.fixture
async def frontend_stub(hass: HomeAssistant) -> None:
    """Stand in for the frontend integration, which the test environment does not include.

    Provides exactly what panel and script registration read and write, on top
    of the real http integration.
    """
    hass.data[frontend.DATA_PANELS] = {}
    hass.data[frontend.DATA_EXTRA_MODULE_URL] = frontend.UrlManager(lambda *_: None, [])
    hass.config.components.add("frontend")
    assert await async_setup_component(hass, "http", {})


def _entry() -> MockConfigEntry:
    return MockConfigEntry(domain=DOMAIN, title=TITLE, data={}, version=5, minor_version=1)


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_registers_the_panel_and_the_bundle_script(
    hass: HomeAssistant, frontend_stub: None
) -> None:
    """The panel and the script for the cards use the same versioned bundle URL."""
    await _setup(hass, _entry())

    bundle_url = _bundle_url(hass, _manifest_version())
    panel = hass.data[frontend.DATA_PANELS][PANEL_URL_PATH]
    assert panel.component_name == "custom"
    assert panel.sidebar_title == TITLE
    assert panel.require_admin is False
    assert panel.config["_panel_custom"]["name"] == PANEL_WEBCOMPONENT
    assert panel.config["_panel_custom"]["module_url"] == bundle_url
    assert bundle_url in hass.data[frontend.DATA_EXTRA_MODULE_URL].urls


async def test_bundle_url_changes_with_the_integration_version(
    hass: HomeAssistant, frontend_stub: None
) -> None:
    """A new integration version yields a new URL, so browsers do not reuse the old bundle."""
    with patch(
        "custom_components.ev_charging.async_get_integration",
        return_value=SimpleNamespace(version="9.9.9"),
    ):
        await _setup(hass, _entry())

    assert _bundle_url(hass, "9.9.9") in hass.data[frontend.DATA_EXTRA_MODULE_URL].urls


async def test_bundle_url_carries_the_start_time_and_keeps_it_when_the_entry_reloads(
    hass: HomeAssistant, frontend_stub: None
) -> None:
    """The URL holds the start time of the process, unchanged by unloading and loading again."""
    entry = _entry()
    await _setup(hass, entry)
    bundle_url = entry.runtime_data.bundle_url
    assert re.search(r"&s=\d+$", bundle_url)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.runtime_data.bundle_url == bundle_url


async def test_bundle_is_served(
    hass: HomeAssistant, frontend_stub: None, hass_client_no_auth: ClientSessionGenerator
) -> None:
    """The bundle file is reachable under the registered path."""
    await _setup(hass, _entry())
    client = await hass_client_no_auth()

    response = await client.get(FRONTEND_STATIC_URL_PATH)

    assert response.status == 200
    assert await response.read() == (FRONTEND_DIR / FRONTEND_BUNDLE_FILENAME).read_bytes()


async def test_unload_removes_the_panel_and_the_script_and_setup_can_repeat(
    hass: HomeAssistant, frontend_stub: None
) -> None:
    """Unloading leaves nothing registered; loading again registers without error."""
    entry = _entry()
    await _setup(hass, entry)
    bundle_url = entry.runtime_data.bundle_url

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert PANEL_URL_PATH not in hass.data[frontend.DATA_PANELS]
    assert bundle_url not in hass.data[frontend.DATA_EXTRA_MODULE_URL].urls

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert PANEL_URL_PATH in hass.data[frontend.DATA_PANELS]
    assert bundle_url in hass.data[frontend.DATA_EXTRA_MODULE_URL].urls


async def test_setup_without_the_frontend_integration_still_succeeds(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Without the frontend integration nothing is registered, and the entry still loads."""
    entry = _entry()
    caplog.set_level(logging.WARNING)

    await _setup(hass, entry)

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.bundle_url is None
    assert frontend.DATA_PANELS not in hass.data
    assert "frontend integration is not loaded" in caplog.text
    assert await hass.config_entries.async_unload(entry.entry_id)


def test_the_bundle_is_a_single_file_that_defines_every_element_of_the_sources() -> None:
    """Exactly one built file ships, and it defines every element main.ts registers.

    A card registered in the sources but missing from the shipped bundle shows
    as "Custom element doesn't exist" on the dashboard, so a bundle that was
    not rebuilt fails here.
    """
    shipped = sorted(path.name for path in FRONTEND_DIR.iterdir() if path.name != ".gitkeep")
    assert shipped == [FRONTEND_BUNDLE_FILENAME]

    main = (FRONTEND_SOURCES / "main.ts").read_text(encoding="utf-8")
    elements = re.findall(r'defineOnce\("([a-z-]+)"', main)
    assert PANEL_WEBCOMPONENT in elements
    assert {"ev-charging-panel-card", "ev-charging-recent-card"} <= set(elements)

    bundle = (FRONTEND_DIR / FRONTEND_BUNDLE_FILENAME).read_text(encoding="utf-8")
    for element in elements:
        assert f'"{element}"' in bundle, f"{element} is missing from the built bundle"


@pytest.mark.parametrize(("language", "expected"), [("en", "Overview"), ("de", "Übersicht")])
async def test_frontend_texts_are_delivered_under_the_key_path_the_bundle_reads(
    hass: HomeAssistant, language: str, expected: str
) -> None:
    """The translation command returns the panel texts under the prefix the bundle strips."""
    prefix = "component.ev_charging.selector.panel.options."

    resources = await async_get_translations(hass, language, "selector", [DOMAIN])

    assert resources[f"{prefix}view_overview"] == expected
    panel_keys = {key.removeprefix(prefix) for key in resources if key.startswith(prefix)}
    bundle = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    assert panel_keys == set(bundle["selector"]["panel"]["options"])


def test_bundle_digest_changes_with_the_file_content(tmp_path: Path) -> None:
    """A rebuilt bundle gets a new URL even when the version stays the same."""
    bundle = tmp_path / "bundle.js"
    bundle.write_text("one", encoding="utf-8")
    first = _bundle_digest(bundle)
    assert first == _bundle_digest(bundle)

    bundle.write_text("two", encoding="utf-8")

    assert _bundle_digest(bundle) != first
    assert _bundle_digest(tmp_path / "missing.js") is None
