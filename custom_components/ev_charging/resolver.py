"""Role resolution, unit detection, and entity registry observation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from awesomeversion import AwesomeVersion
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_registry import EventEntityRegistryUpdatedData
from homeassistant.helpers.event import (
    async_call_later,
    async_track_entity_registry_updated_event,
)
from homeassistant.loader import IntegrationNotFound, async_get_integration

from . import direct_read, mappings
from .const import (
    CHARGE_STATE_DEFAULT,
    DIRECT_READ_RETRIES,
    DIRECT_READ_RETRY_INTERVAL_S,
    DISTANCE_UNIT_FACTORS_TO_KM,
    DOMAIN,
    ENERGY_UNIT_FACTORS_TO_KWH,
    ERROR_CLASS_OK,
    IDENTIFICATION_MAX_AGE_MIN,
    INVALID_CARD_UIDS,
    MAPPING_CLASS_NEUTRAL,
    PLUG_STATE_CONNECTED,
    POWER_UNIT_FACTORS_TO_KW,
    READ_FAILURE_INVALID_VALUE,
    READ_FAILURE_UNREACHABLE,
    ROLE_IDENTIFICATION,
)
from .models import EntityRole, Wallbox, normalize_card_uid

_LOGGER = logging.getLogger(__name__)


async def async_get_mapping(
    hass: HomeAssistant, mapping_id: str | None
) -> mappings.DeviceMapping | None:
    """Return the device mapping a subentry chose, or None if none or an unknown id is stored."""
    if mapping_id is None:
        return None
    return (await mappings.async_get_mappings(hass)).get(mapping_id)


def build_role(hass: HomeAssistant, entity_id: str | None) -> EntityRole | None:
    """Build a role from a freshly selected entity_id (5.1, 5.2, 4.8).

    Captures the registry entry id, when one exists, and the entity's
    current unit_of_measurement.
    """
    if not entity_id:
        return None
    entry = er.async_get(hass).async_get(entity_id)
    state = hass.states.get(entity_id)
    unit = state.attributes.get("unit_of_measurement") if state is not None else None
    return EntityRole(
        entity_id=entity_id,
        registry_entry_id=entry.id if entry is not None else None,
        unit=unit,
    )


def resolve_entity_id(hass: HomeAssistant, role: EntityRole | None) -> str | None:
    """Return a role's current entity_id.

    Prefers the registry entry id (E15). Falls back to the stored entity_id
    for entities without a registry entry (4.8). Returns None if a registry
    entry id is stored but the entry no longer exists.
    """
    if role is None:
        return None
    if role.registry_entry_id is not None:
        entry = er.async_get(hass).async_get(role.registry_entry_id)
        return entry.entity_id if entry is not None else None
    return role.entity_id


def resolve_current_unit(hass: HomeAssistant, role: EntityRole | None) -> str | None:
    """Return the current unit_of_measurement of a role's entity, if any."""
    entity_id = resolve_entity_id(hass, role)
    if entity_id is None:
        return None
    state = hass.states.get(entity_id)
    if state is None:
        return None
    return state.attributes.get("unit_of_measurement")


def unit_changed(role: EntityRole | None, current_unit: str | None) -> bool:
    """Return whether current_unit differs from the unit recorded at assignment (I13)."""
    if role is None or role.unit is None:
        return False
    return current_unit != role.unit


def check_role_unit(
    hass: HomeAssistant,
    role: EntityRole | None,
    *,
    issue_id: str,
    translation_key: str,
    translation_placeholders: dict[str, str],
) -> None:
    """Create or clear the unit-changed repair issue for a numeric role."""
    if role is not None and role.unit is not None:
        current_unit = resolve_current_unit(hass, role)
        if current_unit is not None and unit_changed(role, current_unit):
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=translation_key,
                translation_placeholders=translation_placeholders,
            )
            return
    ir.async_delete_issue(hass, DOMAIN, issue_id)


def _normalize(value: float, unit: str | None, factors: dict[str, float]) -> float | None:
    """Convert value to the canonical unit for factors, or None if unrecognized."""
    if unit is None:
        return None
    factor = factors.get(unit)
    return value * factor if factor is not None else None


def normalize_power_kw(value: float, unit: str | None) -> float | None:
    """Convert a power value to kW."""
    return _normalize(value, unit, POWER_UNIT_FACTORS_TO_KW)


def normalize_energy_kwh(value: float, unit: str | None) -> float | None:
    """Convert an energy value to kWh."""
    return _normalize(value, unit, ENERGY_UNIT_FACTORS_TO_KWH)


def normalize_distance_km(value: float, unit: str | None) -> float | None:
    """Convert a distance value to km."""
    return _normalize(value, unit, DISTANCE_UNIT_FACTORS_TO_KM)


def classify_state(raw_state: str, mapping: dict[str, str], *, default: str) -> tuple[str, bool]:
    """Classify a raw state value using a mapping.

    Returns the class and whether the value was found in the mapping. An
    unmapped value falls back to default instead of raising.
    """
    if raw_state in mapping:
        return mapping[raw_state], True
    return default, False


def classify_charge_state(raw_state: str, mapping: dict[str, str]) -> tuple[str, bool]:
    """Classify a vehicle's raw charge state into one of the four classes (I15)."""
    return classify_state(raw_state, mapping, default=CHARGE_STATE_DEFAULT)


def classify_plug_state(raw_state: str, mapping: dict[str, str]) -> tuple[str, bool]:
    """Classify the wallbox's raw plug state.

    An unmapped value stays connected, so an unrecognized state never ends a
    session on its own.
    """
    return classify_state(raw_state, mapping, default=PLUG_STATE_CONNECTED)


def classify_error_state(raw_state: str, mapping: dict[str, str]) -> tuple[str, bool]:
    """Classify a raw error-role state value. An unmapped value is never an error (E29)."""
    return classify_state(raw_state, mapping, default=ERROR_CLASS_OK)


def classify_with_neutral(
    raw_state: str, mapping: dict[str, str], *, default: str, last_class: str | None
) -> tuple[str | None, bool]:
    """Classify a raw value where a neutral entry keeps the last valid class.

    Returns the class and whether the value was found in the mapping. A value
    the mapping marks neutral yields the last valid class, or None when there
    is none yet, and counts as found. An unmapped value falls back to default.
    """
    klass = mapping.get(raw_state)
    if klass is None:
        return default, False
    if klass == MAPPING_CLASS_NEUTRAL:
        return last_class, True
    return klass, True


def usable_state(state: State | None) -> str | None:
    """Return a state's value, or None while it is missing, unknown or unavailable."""
    if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        return None
    return state.state


def read_number(
    state: State | None, role: EntityRole | None, factors: dict[str, float] | None
) -> float | None:
    """Read a numeric role value, normalized to the canonical unit of factors.

    Returns None if the state is unusable, not a number, or reports a unit
    other than the one recorded at assignment; a changed unit is never
    converted silently. With factors=None the value is returned as it
    stands, for roles without a unit conversion.
    """
    raw = usable_state(state)
    if raw is None or state is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    unit = state.attributes.get("unit_of_measurement")
    if role is not None and role.unit is not None and unit != role.unit:
        return None
    if factors is None:
        return value
    return _normalize(value, unit, factors)


def classify_charge_type(raw_state: str, mapping: dict[str, str]) -> str | None:
    """Classify a raw charge_type value into ac or dc, or None if unmapped."""
    return mapping.get(raw_state)


@callback
def async_track_role_registry(
    hass: HomeAssistant,
    role: EntityRole,
    *,
    on_removed: Callable[[], None],
) -> Callable[[], None] | None:
    """Track entity registry changes for a role backed by a registry entry (4.8).

    Reacts to removal by calling on_removed and logs a rename at INFO level,
    re-subscribing under the new entity_id. Returns None, calling on_removed
    immediately, if the registry entry is already gone. Returns None without
    tracking anything for a role that has no registry entry to track.
    """
    if role.registry_entry_id is None:
        return None

    entry = er.async_get(hass).async_get(role.registry_entry_id)
    if entry is None:
        on_removed()
        return None

    unsub_holder: list[Callable[[], None]] = []

    @callback
    def _handle(event: Event[EventEntityRegistryUpdatedData]) -> None:
        if event.data["action"] == "remove":
            on_removed()
            return
        if event.data["action"] == "update" and "old_entity_id" in event.data:
            _LOGGER.info(
                "Entity for role %s renamed from %s to %s",
                role.registry_entry_id,
                event.data["old_entity_id"],
                event.data["entity_id"],
            )
            unsub_holder[0]()
            unsub_holder[0] = async_track_entity_registry_updated_event(
                hass, [event.data["entity_id"]], _handle
            )

    unsub_holder.append(async_track_entity_registry_updated_event(hass, [entry.entity_id], _handle))

    def _unsub() -> None:
        unsub_holder[0]()

    return _unsub


async def async_integration_meets_min_version(
    hass: HomeAssistant, domain: str, min_version: str
) -> bool | None:
    """Return whether an installed integration is at least min_version.

    Returns None if the integration is not installed at all (4.7, O20).
    """
    try:
        integration = await async_get_integration(hass, domain)
    except IntegrationNotFound:
        return None
    return AwesomeVersion(integration.version) >= AwesomeVersion(min_version)


def _register_request(
    wallbox: Wallbox, device_mapping: mappings.DeviceMapping | None
) -> tuple[direct_read.Endpoint, direct_read.RegisterSpec] | None:
    """Return what to read to get the identification from the device, or None.

    None when the wallbox takes the identification from an entity, when the
    direct read is off, or when the chosen device has no register for it.
    """
    if not (wallbox.direct_read_enabled and wallbox.identification_from_register and wallbox.host):
        return None
    register = device_mapping.role_register(ROLE_IDENTIFICATION) if device_mapping else None
    if register is None:
        return None
    return (
        direct_read.Endpoint(host=wallbox.host, port=wallbox.port, unit_id=wallbox.unit_id),
        direct_read.RegisterSpec(
            address=register["address"],
            count=register["count"],
            decode=register["decode"],
            output=register["format"],
        ),
    )


class IdentificationReader:
    """Supplies the identification value a session is matched on.

    The value comes from an entity or, when the wallbox is set up for it,
    from a register of the device that is read when the session starts. A
    read that fails is repeated a few times, spaced apart. The caller only
    sees the value, and whether it is still being retrieved.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        wallbox: Wallbox,
        device_mapping: mappings.DeviceMapping | None,
    ) -> None:
        """Prepare the reader for the wallbox's identification role."""
        self._hass = hass
        self._wallbox = wallbox
        self._request = _register_request(wallbox, device_mapping)
        self._unsub: Callable[[], None] | None = None
        self._on_done: Callable[[], None] | None = None
        self._generation = 0
        self._failed_reads = 0
        self._pending = False
        self._value: str | None = None
        self._failure: str | None = None

    async def async_prepare(self) -> None:
        """Load what reading the register needs, if that is where the value comes from."""
        if self._request is None:
            return
        try:
            await direct_read.async_prepare(self._hass)
        except ImportError:
            _LOGGER.error("The Modbus client library is missing; the wallbox is not read directly")
            self._request = None

    @property
    def pending(self) -> bool:
        """Whether the value is still being retrieved."""
        return self._pending

    @property
    def failure(self) -> str | None:
        """How the last completed retrieval failed, or None if it did not."""
        return self._failure

    def begin(self, on_done: Callable[[], None]) -> None:
        """Start retrieving the value, for a session that just started.

        on_done is called once, when the retrieval is complete. There is
        nothing to retrieve for an entity, which is read when asked for.
        """
        self.cancel()
        if self._request is None:
            return
        self._pending = True
        self._on_done = on_done
        self._schedule(0)

    def cancel(self) -> None:
        """Stop retrieving and forget what was retrieved."""
        self._generation += 1
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        self._pending = False
        self._on_done = None
        self._failed_reads = 0
        self._value = None
        self._failure = None

    def value(self, session_start: datetime) -> str | None:
        """Return the identification of the session that started at session_start.

        The value is normalized. None when there is none, when it is not a
        valid identifier, or, for an entity, when it changed too long before
        the session started.
        """
        if self._request is not None:
            return self._value
        entity_id = resolve_entity_id(self._hass, self._wallbox.identification)
        state = self._hass.states.get(entity_id) if entity_id else None
        raw = usable_state(state)
        if raw is None or state is None:
            return None
        normalized = normalize_card_uid(raw)
        if not normalized or normalized in INVALID_CARD_UIDS:
            return None
        if state.last_changed < session_start - timedelta(minutes=IDENTIFICATION_MAX_AGE_MIN):
            return None
        return normalized

    def _schedule(self, delay_s: float) -> None:
        """Run the next read after delay_s."""
        self._unsub = async_call_later(self._hass, delay_s, self._async_read)

    async def _async_read(self, _now: datetime) -> None:
        """Read the register once and either finish or schedule a further read."""
        assert self._request is not None
        self._unsub = None
        generation = self._generation
        endpoint, spec = self._request
        try:
            raw = await direct_read.async_read_register(self._hass, endpoint, spec)
        except Exception:
            _LOGGER.exception("Reading the identification from the wallbox raised an error")
            raw = None
        if generation != self._generation:
            return

        value: str | None = None
        failure: str | None = None
        if raw is None:
            failure = READ_FAILURE_UNREACHABLE
        elif raw == 0:
            failure = READ_FAILURE_INVALID_VALUE
        else:
            text = direct_read.format_value(raw, spec.output)
            value = normalize_card_uid(text) if text else None
            if not value or value in INVALID_CARD_UIDS:
                value, failure = None, READ_FAILURE_INVALID_VALUE

        if failure is not None:
            self._failed_reads += 1
            if self._failed_reads <= DIRECT_READ_RETRIES:
                self._schedule(DIRECT_READ_RETRY_INTERVAL_S)
                return
        self._pending = False
        self._value = value
        self._failure = failure
        on_done, self._on_done = self._on_done, None
        if on_done is not None:
            on_done()
