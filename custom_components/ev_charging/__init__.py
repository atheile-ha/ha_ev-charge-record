"""The ev_charging integration."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.loader import async_get_integration

from . import mappings, problems, resolver, services, websocket
from .const import (
    CONF_VEHICLE_SEQUENCE,
    CONF_WALLBOX_SEQUENCE,
    DOMAIN,
    FRONTEND_BUNDLE_FILENAME,
    FRONTEND_STATIC_URL_PATH,
    PANEL_ICON,
    PANEL_URL_PATH,
    PANEL_WEBCOMPONENT,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
)
from .models import EntityRole, HubSettings, Vehicle, Wallbox
from .session_manager import SessionManager

_LOGGER = logging.getLogger(__name__)

_DATA_STATIC_PATH_REGISTERED = "frontend_static_path_registered"

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


@dataclass
class EvChargingRuntimeData:
    """Runtime data attached to the config entry while it is set up."""

    unsub_listeners: list[Callable[[], None]]
    # URL under which the frontend bundle was registered, None if the frontend
    # integration is not loaded and nothing was registered.
    bundle_url: str | None = None
    # Captures the sessions of the wallbox. None if no wallbox is configured.
    manager: SessionManager | None = None


type EvChargingConfigEntry = ConfigEntry[EvChargingRuntimeData]


def _wallbox_roles(wallbox: Wallbox) -> list[tuple[str, EntityRole | None, bool]]:
    """List (role_name, role, has_unit) for a wallbox's entity roles."""
    return [
        ("charge_power", wallbox.charge_power, True),
        ("energy_total", wallbox.energy_total, True),
        ("energy_session", wallbox.energy_session, True),
        ("plug_state", wallbox.plug_state, False),
        ("identification", wallbox.identification, False),
        ("error", wallbox.error, False),
    ]


def _vehicle_roles(vehicle: Vehicle) -> list[tuple[str, EntityRole | None, bool]]:
    """List (role_name, role, has_unit) for a vehicle's entity roles."""
    return [
        ("soc", vehicle.soc, True),
        ("soc_target", vehicle.soc_target, True),
        ("odometer", vehicle.odometer, True),
        ("charge_state", vehicle.charge_state, False),
        ("charge_type", vehicle.charge_type, False),
        ("plug_state", vehicle.plug_state, False),
        ("energy_session", vehicle.energy_session, True),
        ("location", vehicle.location, False),
        ("charge_end", vehicle.charge_end, False),
        ("charge_power", vehicle.charge_power, True),
        ("range", vehicle.range, True),
    ]


def _hub_roles(settings: HubSettings) -> list[tuple[str, EntityRole | None, bool]]:
    """List (role_name, role, has_unit) for the hub's entity roles."""
    return [
        ("grid_power", settings.grid_power, True),
        ("grid_import", settings.grid_import, True),
        ("grid_export", settings.grid_export, True),
        ("price_grid", settings.price_grid, True),
        ("price_feed_in", settings.price_feed_in, True),
    ]


def _watch_roles(
    hass: HomeAssistant,
    *,
    subentry_id: str,
    subentry_title: str,
    roles: list[tuple[str, EntityRole | None, bool]],
    unsub_listeners: list[Callable[[], None]],
) -> None:
    """Start registry tracking and run the one-time unit check for a set of roles."""
    for role_name, role, has_unit in roles:
        if role is None:
            continue

        def _on_removed(role_name: str = role_name) -> None:
            problems.async_create_role_removed_issue(
                hass, subentry_id=subentry_id, role_name=role_name, subentry_title=subentry_title
            )

        unsub = resolver.async_track_role_registry(hass, role, on_removed=_on_removed)
        if unsub is not None:
            unsub_listeners.append(unsub)
        else:
            problems.async_clear_role_removed_issue(
                hass, subentry_id=subentry_id, role_name=role_name
            )

        if has_unit:
            resolver.check_role_unit(
                hass,
                role,
                issue_id=problems.role_unit_changed_issue_id(subentry_id, role_name),
                translation_key="role_unit_changed",
                translation_placeholders={"role": role_name, "subentry_title": subentry_title},
            )


async def _async_check_mapping_min_version(
    hass: HomeAssistant, *, subentry_id: str, subentry_title: str, mapping_id: str | None
) -> None:
    """Check a subentry's chosen mapping source against its min_version (4.7, O20)."""
    if mapping_id is None:
        return
    all_mappings = await mappings.async_get_mappings(hass)
    mapping = all_mappings.get(mapping_id)
    if mapping is None:
        return
    meets = await resolver.async_integration_meets_min_version(
        hass, mapping.integration_domain, mapping.min_version
    )
    problems.check_mapping_source_below_min_version(
        hass,
        below_min_version=meets is not True,
        subentry_id=subentry_id,
        subentry_title=subentry_title,
        device_label=mapping.device_label,
        integration_name=mapping.integration_name,
        min_version=mapping.min_version,
    )


def _bundle_digest(path: Path) -> str | None:
    """Return a short digest of the bundle file, or None if it cannot be read."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return None


async def _async_register_frontend(hass: HomeAssistant) -> str | None:
    """Serve the frontend bundle and register the panel and the dashboard cards.

    Returns the bundle URL, or None if the frontend integration is not loaded.
    The URL carries the integration version and a digest of the bundle file,
    so browsers and the companion apps fetch a changed bundle instead of
    reusing a cached one, even when the version did not change.
    """
    if "frontend" not in hass.config.components:
        _LOGGER.warning("The frontend integration is not loaded; panel and cards are unavailable")
        return None

    integration = await async_get_integration(hass, DOMAIN)
    bundle_path = Path(__file__).parent / "frontend" / FRONTEND_BUNDLE_FILENAME
    digest = await hass.async_add_executor_job(_bundle_digest, bundle_path)
    if digest is None:
        _LOGGER.warning("The frontend bundle %s cannot be read", bundle_path)
    bundle_url = f"{FRONTEND_STATIC_URL_PATH}?v={integration.version}"
    if digest is not None:
        bundle_url += f"&h={digest}"

    domain_data = hass.data.setdefault(DOMAIN, {})
    if not domain_data.get(_DATA_STATIC_PATH_REGISTERED):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(FRONTEND_STATIC_URL_PATH, str(bundle_path), cache_headers=True)]
        )
        domain_data[_DATA_STATIC_PATH_REGISTERED] = True

    frontend.add_extra_js_url(hass, bundle_url)
    if not frontend.async_panel_exists(hass, PANEL_URL_PATH):
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_URL_PATH,
            webcomponent_name=PANEL_WEBCOMPONENT,
            sidebar_title=TITLE,
            sidebar_icon=PANEL_ICON,
            module_url=bundle_url,
            require_admin=False,
        )
    return bundle_url


async def async_setup_entry(hass: HomeAssistant, entry: EvChargingConfigEntry) -> bool:
    """Set up ev_charging from a config entry."""
    unsub_listeners: list[callable] = []
    settings = HubSettings.from_dict(entry.data)
    _watch_roles(
        hass,
        subentry_id=entry.entry_id,
        subentry_title=entry.title,
        roles=_hub_roles(settings),
        unsub_listeners=unsub_listeners,
    )

    for subentry in entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_WALLBOX:
            wallbox = Wallbox.from_dict(subentry.data)
            _watch_roles(
                hass,
                subentry_id=subentry.subentry_id,
                subentry_title=subentry.title,
                roles=_wallbox_roles(wallbox),
                unsub_listeners=unsub_listeners,
            )
            await _async_check_mapping_min_version(
                hass,
                subentry_id=subentry.subentry_id,
                subentry_title=subentry.title,
                mapping_id=wallbox.mapping_id,
            )
        elif subentry.subentry_type == SUBENTRY_TYPE_VEHICLE:
            vehicle = Vehicle.from_dict(subentry.data)
            _watch_roles(
                hass,
                subentry_id=subentry.subentry_id,
                subentry_title=subentry.title,
                roles=_vehicle_roles(vehicle),
                unsub_listeners=unsub_listeners,
            )
            await _async_check_mapping_min_version(
                hass,
                subentry_id=subentry.subentry_id,
                subentry_title=subentry.title,
                mapping_id=vehicle.mapping_id,
            )

    websocket.async_setup_websocket(hass)
    bundle_url = await _async_register_frontend(hass)
    manager = SessionManager(hass, entry)
    if not await manager.async_setup():
        manager = None
    entry.runtime_data = EvChargingRuntimeData(
        unsub_listeners=unsub_listeners, bundle_url=bundle_url, manager=manager
    )
    services.async_setup_services(hass)
    _detach_devices(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


def _detach_devices(hass: HomeAssistant, entry: EvChargingConfigEntry) -> None:
    """Take the entities off the devices earlier versions gave them and remove those devices.

    The entities belong to the subentry of the wallbox and have no device. Entity
    ids, names and the enabled state stay as they were.
    """
    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    for entity in er.async_entries_for_config_entry(entities, entry.entry_id):
        if entity.device_id is not None:
            entities.async_update_entity(entity.entity_id, device_id=None)
    for device in dr.async_entries_for_config_entry(devices, entry.entry_id):
        devices.async_update_device(device.id, remove_config_entry_id=entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: EvChargingConfigEntry) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    if entry.runtime_data.manager is not None:
        await entry.runtime_data.manager.async_unload()
    for unsub in entry.runtime_data.unsub_listeners:
        unsub()
    if entry.runtime_data.bundle_url is not None:
        frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
        frontend.remove_extra_js_url(hass, entry.runtime_data.bundle_url)
    services.async_unload_services(hass)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate the hub entry and its subentries to the current schema."""
    if entry.version == 1:
        from_version = f"{entry.version}.{entry.minor_version}"
        for subentry in entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_WALLBOX:
                wallbox = Wallbox.from_dict(subentry.data)
                hass.config_entries.async_update_subentry(entry, subentry, data=wallbox.to_dict())
            elif subentry.subentry_type == SUBENTRY_TYPE_VEHICLE:
                vehicle = Vehicle.from_dict(subentry.data)
                hass.config_entries.async_update_subentry(entry, subentry, data=vehicle.to_dict())

        data = {
            CONF_WALLBOX_SEQUENCE: entry.data.get(CONF_WALLBOX_SEQUENCE, 0),
            CONF_VEHICLE_SEQUENCE: entry.data.get(CONF_VEHICLE_SEQUENCE, 0),
            **HubSettings.from_dict(entry.data).to_dict(),
        }
        hass.config_entries.async_update_entry(entry, data=data, version=2, minor_version=1)
        _LOGGER.info(
            "Migrated ev_charging config entry %s from version %s to 2.1",
            entry.entry_id,
            from_version,
        )

    if entry.version == 2:
        from_version = f"{entry.version}.{entry.minor_version}"
        for subentry in entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_WALLBOX:
                wallbox = Wallbox.from_dict(subentry.data)
                hass.config_entries.async_update_subentry(entry, subentry, data=wallbox.to_dict())
            elif subentry.subentry_type == SUBENTRY_TYPE_VEHICLE:
                vehicle = Vehicle.from_dict(subentry.data)
                hass.config_entries.async_update_subentry(entry, subentry, data=vehicle.to_dict())

        data = {**entry.data, **HubSettings.from_dict(entry.data).to_dict()}
        hass.config_entries.async_update_entry(entry, data=data, version=3, minor_version=1)
        _LOGGER.info(
            "Migrated ev_charging config entry %s from version %s to 3.1",
            entry.entry_id,
            from_version,
        )

    if entry.version == 3:
        from_version = f"{entry.version}.{entry.minor_version}"
        for subentry in entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_WALLBOX:
                wallbox = Wallbox.from_dict(subentry.data)
                hass.config_entries.async_update_subentry(entry, subentry, data=wallbox.to_dict())
            elif subentry.subentry_type == SUBENTRY_TYPE_VEHICLE:
                vehicle = Vehicle.from_dict(subentry.data)
                hass.config_entries.async_update_subentry(entry, subentry, data=vehicle.to_dict())

        hass.config_entries.async_update_entry(entry, version=4, minor_version=1)
        _LOGGER.info(
            "Migrated ev_charging config entry %s from version %s to 4.1, discarding stored "
            "state mappings; wallboxes and vehicles need their mapping device reassigned",
            entry.entry_id,
            from_version,
        )

    if entry.version == 4:
        from_version = f"{entry.version}.{entry.minor_version}"
        for subentry in entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_WALLBOX:
                wallbox = Wallbox.from_dict(subentry.data)
                hass.config_entries.async_update_subentry(entry, subentry, data=wallbox.to_dict())

        hass.config_entries.async_update_entry(entry, version=5, minor_version=1)
        _LOGGER.info(
            "Migrated ev_charging config entry %s from version %s to 5.1, adding the direct "
            "read settings of the wallbox with the direct read switched off",
            entry.entry_id,
            from_version,
        )
    return True
