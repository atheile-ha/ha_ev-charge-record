"""Repair issues for source entity problems (4.8, 5.3, 12.3)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN, ISSUE_ROLE_ENTITY_REMOVED, ISSUE_ROLE_UNIT_CHANGED


def role_removed_issue_id(subentry_id: str, role_name: str) -> str:
    """Return the stable issue id for a role whose entity was removed."""
    return f"{ISSUE_ROLE_ENTITY_REMOVED}_{subentry_id}_{role_name}"


def role_unit_changed_issue_id(subentry_id: str, role_name: str) -> str:
    """Return the stable issue id for a role whose unit changed."""
    return f"{ISSUE_ROLE_UNIT_CHANGED}_{subentry_id}_{role_name}"


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
