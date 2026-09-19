"""Repair issues for source entity problems (4.8, 5.3, 4.7, 12.3)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import (
    DOMAIN,
    ISSUE_COUNTER_SWITCHED,
    ISSUE_MAPPING_SOURCE_BELOW_MIN_VERSION,
    ISSUE_ROLE_ENTITY_REMOVED,
    ISSUE_ROLE_UNIT_CHANGED,
    ISSUE_UNKNOWN_CARD,
    ISSUE_UNKNOWN_MAPPING_VALUE,
)


def role_removed_issue_id(subentry_id: str, role_name: str) -> str:
    """Return the stable issue id for a role whose entity was removed."""
    return f"{ISSUE_ROLE_ENTITY_REMOVED}_{subentry_id}_{role_name}"


def role_unit_changed_issue_id(subentry_id: str, role_name: str) -> str:
    """Return the stable issue id for a role whose unit changed."""
    return f"{ISSUE_ROLE_UNIT_CHANGED}_{subentry_id}_{role_name}"


def unknown_mapping_value_issue_id(subentry_id: str, role_name: str) -> str:
    """Return the stable issue id for a role whose raw value is missing from its mapping."""
    return f"{ISSUE_UNKNOWN_MAPPING_VALUE}_{subentry_id}_{role_name}"


def mapping_source_below_min_version_issue_id(subentry_id: str) -> str:
    """Return the stable issue id for a subentry whose mapping source is too old or missing."""
    return f"{ISSUE_MAPPING_SOURCE_BELOW_MIN_VERSION}_{subentry_id}"


def async_create_role_removed_issue(
    hass: HomeAssistant, *, subentry_id: str, role_name: str, subentry_title: str
) -> None:
    """Create the repair issue for a role whose entity was removed (4.8)."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        role_removed_issue_id(subentry_id, role_name),
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="role_entity_removed",
        translation_placeholders={"role": role_name, "subentry_title": subentry_title},
    )


def async_clear_role_removed_issue(
    hass: HomeAssistant, *, subentry_id: str, role_name: str
) -> None:
    """Clear the repair issue for a role whose entity was removed."""
    ir.async_delete_issue(hass, DOMAIN, role_removed_issue_id(subentry_id, role_name))


def check_unknown_mapping_value(
    hass: HomeAssistant,
    *,
    found: bool,
    subentry_id: str,
    subentry_title: str,
    role_name: str,
    raw_value: str,
) -> None:
    """Create or clear the repair issue for a raw value missing from its mapping (4.7).

    Offers no way to assign the value by hand (E33): the mapping comes from
    the integration, not from the user.
    """
    issue_id = unknown_mapping_value_issue_id(subentry_id, role_name)
    if not found:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="unknown_mapping_value",
            translation_placeholders={
                "role": role_name,
                "subentry_title": subentry_title,
                "raw_value": raw_value,
            },
        )
        return
    ir.async_delete_issue(hass, DOMAIN, issue_id)


def check_mapping_source_below_min_version(
    hass: HomeAssistant,
    *,
    below_min_version: bool,
    subentry_id: str,
    subentry_title: str,
    device_label: str,
    integration_name: str,
    min_version: str,
) -> None:
    """Create or clear the repair issue for a mapping source below min_version (4.7, O20)."""
    issue_id = mapping_source_below_min_version_issue_id(subentry_id)
    if below_min_version:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="mapping_source_below_min_version",
            translation_placeholders={
                "subentry_title": subentry_title,
                "device": device_label,
                "integration_name": integration_name,
                "min_version": min_version,
            },
        )
        return
    ir.async_delete_issue(hass, DOMAIN, issue_id)


def unknown_card_issue_id(wallbox_id: str) -> str:
    """Return the stable issue id for a card the wallbox reported but no vehicle holds."""
    return f"{ISSUE_UNKNOWN_CARD}_{wallbox_id}"


def async_create_unknown_card_issue(
    hass: HomeAssistant, *, wallbox_id: str, wallbox_title: str
) -> None:
    """Create the repair issue for a card that no vehicle holds.

    The card itself is deliberately not named in the issue.
    """
    ir.async_create_issue(
        hass,
        DOMAIN,
        unknown_card_issue_id(wallbox_id),
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_UNKNOWN_CARD,
        translation_placeholders={"wallbox_title": wallbox_title},
    )


def async_clear_unknown_card_issue(hass: HomeAssistant, *, wallbox_id: str) -> None:
    """Clear the repair issue for an unknown card."""
    ir.async_delete_issue(hass, DOMAIN, unknown_card_issue_id(wallbox_id))


def counter_switched_issue_id(wallbox_id: str) -> str:
    """Return the stable issue id for a wallbox whose authoritative counter changed."""
    return f"{ISSUE_COUNTER_SWITCHED}_{wallbox_id}"


def async_create_counter_switched_issue(
    hass: HomeAssistant, *, wallbox_id: str, wallbox_title: str, counter: str
) -> None:
    """Create the repair issue for an automatic change of the authoritative energy counter."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        counter_switched_issue_id(wallbox_id),
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_COUNTER_SWITCHED,
        translation_placeholders={"wallbox_title": wallbox_title, "counter": counter},
    )
