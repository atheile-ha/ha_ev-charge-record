"""Loading, validation and lookup of the bundled device mapping files (4.7)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CHARGE_STATE_CLASSES,
    CHARGE_TYPES,
    DOMAIN,
    ERROR_CLASSES,
    MAPPING_CLASS_NEUTRAL,
    MAPPING_FORMAT_VERSION,
    MAX_DIRECT_READ_UNIT_ID,
    MIN_DIRECT_READ_UNIT_ID,
    MODBUS_FUNCTION_READ_HOLDING_REGISTERS,
    MODBUS_MAX_REGISTER_ADDRESS,
    MODBUS_MAX_REGISTER_COUNT,
    PLUG_STATE_CLASSES,
    REGISTER_DECODE_UINT32_BIG_ENDIAN,
    REGISTER_DECODES,
    REGISTER_FORMATS,
    REGISTER_ROLES,
    ROLE_CHARGE_STATE,
    ROLE_CHARGE_TYPE,
    ROLE_ERROR,
    ROLE_PLUG_STATE,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
)

_LOGGER = logging.getLogger(__name__)

MAPPINGS_DIR = Path(__file__).parent / "mappings"

# The set of classes a role's raw values may resolve to, in addition to
# MAPPING_CLASS_NEUTRAL. Roles not listed here carry a register instead of
# values and are not validated against a class set.
_ROLE_CLASSES: dict[str, tuple[str, ...]] = {
    ROLE_PLUG_STATE: PLUG_STATE_CLASSES,
    ROLE_ERROR: ERROR_CLASSES,
    ROLE_CHARGE_STATE: CHARGE_STATE_CLASSES,
    ROLE_CHARGE_TYPE: CHARGE_TYPES,
}

_VALID_KINDS = (SUBENTRY_TYPE_WALLBOX, SUBENTRY_TYPE_VEHICLE)


@dataclass(frozen=True, slots=True)
class MappingRole:
    """One role entry of a device mapping file (4.7)."""

    values: dict[str, str] | None = None
    register: dict[str, Any] | None = None
    source_channel: str | None = None
    source_entity_suffix: str | None = None
    note_key: str | None = None


@dataclass(frozen=True, slots=True)
class DeviceMapping:
    """A validated, parsed device mapping file (4.7)."""

    id: str
    kind: str
    integration_domain: str
    integration_name: str
    integration_short_name: str
    min_version: str
    device_manufacturer: str
    device_model: str
    roles: dict[str, MappingRole] = field(default_factory=dict)

    @property
    def device_label(self) -> str:
        """Return the device's display label, including its source integration.

        The same physical device connected through a different integration is
        not the same mapping (E33): the raw values come from the source
        integration, not from the device itself. Naming it in the label
        prevents picking this entry for an unrelated connection path. Device
        and integration names are proper nouns, not translated.

        A wallbox is one of several devices behind a shared gateway
        integration, so it is named by manufacturer and model with the
        integration as a short qualifier. A vehicle mapping corresponds to
        exactly one connected service, so the integration's short name alone
        already identifies it; repeating device.model would just restate it.
        """
        if self.kind == SUBENTRY_TYPE_VEHICLE:
            return self.integration_short_name
        return f"{self.device_manufacturer} {self.device_model} (via {self.integration_short_name})"

    def role_values(self, role: str) -> dict[str, str]:
        """Return a role's raw-value-to-class mapping, or an empty dict if the role has none."""
        role_entry = self.roles.get(role)
        if role_entry is None or role_entry.values is None:
            return {}
        return role_entry.values

    def role_register(self, role: str) -> dict[str, Any] | None:
        """Return a role's register description, or None if the role has none."""
        role_entry = self.roles.get(role)
        return role_entry.register if role_entry is not None else None


def _is_int_in_range(value: Any, low: int, high: int) -> bool:
    """Whether value is an integer, and not a boolean, within low and high."""
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def _register_error(register: dict[str, Any]) -> str | None:
    """Return why a register entry is not acceptable, or None if it is.

    Only reading holding registers (function code 3) can be expressed, and
    only the decodings and formats the reader implements.
    """
    if register.get("function_code") != MODBUS_FUNCTION_READ_HOLDING_REGISTERS:
        return "function_code must be 3"
    if not _is_int_in_range(register.get("address"), 0, MODBUS_MAX_REGISTER_ADDRESS):
        return "address must be an integer from 0 to 65535"
    if not _is_int_in_range(register.get("count"), 1, MODBUS_MAX_REGISTER_COUNT):
        return "count must be 1 or 2"
    if register.get("decode") not in REGISTER_DECODES:
        return f"decode must be one of {REGISTER_DECODES}"
    if register["decode"] == REGISTER_DECODE_UINT32_BIG_ENDIAN and register["count"] != 2:
        return "decode uint32 needs count 2"
    if register.get("format") not in REGISTER_FORMATS:
        return f"format must be one of {REGISTER_FORMATS}"
    unit_id_default = register.get("unit_id_default")
    if unit_id_default is not None and not _is_int_in_range(
        unit_id_default, MIN_DIRECT_READ_UNIT_ID, MAX_DIRECT_READ_UNIT_ID
    ):
        return "unit_id_default must be an integer from 0 to 255"
    return None


def _parse_role(role_name: str, raw_role: Any, *, mapping_id: str) -> MappingRole | None:
    """Parse and validate one role entry. Returns None if invalid."""
    if not isinstance(raw_role, dict):
        _LOGGER.error("Mapping %s: role %s is not an object", mapping_id, role_name)
        return None

    raw_values = raw_role.get("values")
    register = raw_role.get("register")
    if raw_values is None and register is None:
        _LOGGER.error("Mapping %s: role %s has neither values nor register", mapping_id, role_name)
        return None

    values: dict[str, str] | None = None
    if raw_values is not None:
        if not isinstance(raw_values, dict) or not raw_values:
            _LOGGER.error(
                "Mapping %s: role %s values must be a non-empty object", mapping_id, role_name
            )
            return None
        allowed = (*_ROLE_CLASSES.get(role_name, ()), MAPPING_CLASS_NEUTRAL)
        for raw_value, klass in raw_values.items():
            if not isinstance(raw_value, str) or klass not in allowed:
                _LOGGER.error(
                    "Mapping %s: role %s has value %r mapped to invalid class %r",
                    mapping_id,
                    role_name,
                    raw_value,
                    klass,
                )
                return None
        values = dict(raw_values)

    if register is not None:
        if not isinstance(register, dict):
            _LOGGER.error("Mapping %s: role %s register must be an object", mapping_id, role_name)
            return None
        if role_name not in REGISTER_ROLES:
            _LOGGER.error(
                "Mapping %s: role %s cannot be read from a register", mapping_id, role_name
            )
            return None
        register_error = _register_error(register)
        if register_error is not None:
            _LOGGER.error(
                "Mapping %s: role %s has an invalid register: %s",
                mapping_id,
                role_name,
                register_error,
            )
            return None

    return MappingRole(
        values=values,
        register=register,
        source_channel=raw_role.get("source_channel"),
        source_entity_suffix=raw_role.get("source_entity_suffix"),
        note_key=raw_role.get("note_key"),
    )


def _parse_mapping(raw: Any, *, filename: str) -> DeviceMapping | None:
    """Validate and parse one mapping file's already-decoded JSON content."""
    if not isinstance(raw, dict):
        _LOGGER.error("Mapping file %s does not contain a JSON object", filename)
        return None

    if raw.get("format_version") != MAPPING_FORMAT_VERSION:
        _LOGGER.error(
            "Mapping file %s has unsupported format_version %r",
            filename,
            raw.get("format_version"),
        )
        return None

    mapping_id = raw.get("id")
    kind = raw.get("kind")
    integration = raw.get("integration")
    device = raw.get("device")
    roles = raw.get("roles")

    if not isinstance(mapping_id, str) or not mapping_id:
        _LOGGER.error("Mapping file %s has no valid id", filename)
        return None
    if kind not in _VALID_KINDS:
        _LOGGER.error("Mapping %s: kind must be one of %s", mapping_id, _VALID_KINDS)
        return None
    if not isinstance(integration, dict):
        _LOGGER.error("Mapping %s: integration is missing", mapping_id)
        return None
    domain = integration.get("domain")
    name = integration.get("name")
    short_name = integration.get("short_name")
    min_version = integration.get("min_version")
    if not all(
        isinstance(value, str) and value for value in (domain, name, short_name, min_version)
    ):
        _LOGGER.error(
            "Mapping %s: integration.domain, .name, .short_name and .min_version are required",
            mapping_id,
        )
        return None
    if not isinstance(device, dict):
        _LOGGER.error("Mapping %s: device is missing", mapping_id)
        return None
    manufacturer = device.get("manufacturer")
    model = device.get("model")
    if not all(isinstance(value, str) and value for value in (manufacturer, model)):
        _LOGGER.error("Mapping %s: device.manufacturer and .model are required", mapping_id)
        return None
    if not isinstance(roles, dict) or not roles:
        _LOGGER.error("Mapping %s: roles is missing or empty", mapping_id)
        return None

    parsed_roles: dict[str, MappingRole] = {}
    for role_name, raw_role in roles.items():
        parsed_role = _parse_role(role_name, raw_role, mapping_id=mapping_id)
        if parsed_role is None:
            return None
        parsed_roles[role_name] = parsed_role

    return DeviceMapping(
        id=mapping_id,
        kind=kind,
        integration_domain=domain,
        integration_name=name,
        integration_short_name=short_name,
        min_version=min_version,
        device_manufacturer=manufacturer,
        device_model=model,
        roles=parsed_roles,
    )


def load_all(mappings_dir: Path) -> dict[str, DeviceMapping]:
    """Load and validate every mapping file in mappings_dir.

    Blocking; call via the executor. A file that fails validation is
    skipped and logged, not raised. Files that share an id are all skipped
    and logged, since the id is the only way to tell two devices apart.
    """
    parsed_by_file: dict[str, DeviceMapping] = {}
    for path in sorted(mappings_dir.glob("*.json")):
        try:
            with path.open(encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError) as err:
            _LOGGER.error("Mapping file %s could not be read: %s", path.name, err)
            continue
        parsed = _parse_mapping(raw, filename=path.name)
        if parsed is not None:
            parsed_by_file[path.name] = parsed

    by_id: dict[str, list[str]] = {}
    for filename, mapping in parsed_by_file.items():
        by_id.setdefault(mapping.id, []).append(filename)

    result: dict[str, DeviceMapping] = {}
    for mapping_id, filenames in by_id.items():
        if len(filenames) > 1:
            _LOGGER.error(
                "Mapping id %s is used by more than one file (%s); none of them are loaded",
                mapping_id,
                ", ".join(sorted(filenames)),
            )
            continue
        result[mapping_id] = parsed_by_file[filenames[0]]
    return result


async def async_get_mappings(hass: HomeAssistant) -> dict[str, DeviceMapping]:
    """Return the cached, validated mapping table, loading it on first use."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    cached = domain_data.get("mappings")
    if cached is not None:
        return cached
    loaded = await hass.async_add_executor_job(load_all, MAPPINGS_DIR)
    domain_data["mappings"] = loaded
    return loaded


def mappings_for_kind(mappings: dict[str, DeviceMapping], kind: str) -> list[DeviceMapping]:
    """Return the mappings of a given kind, sorted by device label."""
    return sorted((m for m in mappings.values() if m.kind == kind), key=lambda m: m.device_label)
