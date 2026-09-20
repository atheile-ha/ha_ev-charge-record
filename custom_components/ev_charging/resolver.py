"""Role resolution, unit detection, and entity registry observation."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

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
from homeassistant.util import dt as dt_util

from . import direct_read, mappings
from .const import (
    CHARGE_STATE_DEFAULT,
    DIRECT_READ_FIRST_DELAY_S,
    DIRECT_READ_INTERVAL_S,
    DIRECT_READ_MAX_READS,
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
    READ_STATE_READ,
    READ_STATE_READING,
    READ_STATE_UNREADABLE,
    READ_STATE_WAITING,
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


class ReadEvent(StrEnum):
    """What the reader reports to its owner."""

    PROGRESS = "progress"
    VALUE = "value"
    EXHAUSTED = "exhausted"


@dataclass(frozen=True, slots=True)
class ReadProgress:
    """Where the reading of the identification stands."""

    state: str
    sequence: int
    attempt: int
    max_attempts: int


class IdentificationReader:
    """Supplies the identification value a session is matched on.

    The value comes from an entity or, when the wallbox is set up for it,
    from a register of the device. The register is read in at most two
    sequences per session: the first starts a fixed time after the session
    began, the second with the first charging phase and only if the first
    delivered nothing. A sequence reads at a fixed interval, at most a fixed
    number of times, and stops with the first valid value. The caller never
    waits for a read: it asks for the value when it needs it and is told
    through a callback when a value arrives later.
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
        self._task: asyncio.Task[None] | None = None
        self._on_event: Callable[[ReadEvent], None] | None = None
        self._generation = 0
        self._active = False
        self._reading = False
        self._sequence = 0
        self._attempts = 0
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
    def failure(self) -> str | None:
        """How the last read failed once both sequences ended without a value, else None."""
        return self._failure

    @property
    def progress(self) -> ReadProgress | None:
        """Where the reading stands; None for an entity or while no session is being read."""
        if self._request is None or not self._active:
            return None
        if self._value is not None:
            state = READ_STATE_READ
        elif self._reading:
            return ReadProgress(
                READ_STATE_READING, self._sequence, self._attempts + 1, DIRECT_READ_MAX_READS
            )
        elif self._failure is not None:
            state = READ_STATE_UNREADABLE
        else:
            state = READ_STATE_WAITING
        return ReadProgress(state, self._sequence, self._attempts, DIRECT_READ_MAX_READS)

    def begin(self, on_event: Callable[[ReadEvent], None], *, since: datetime) -> None:
        """Start the first sequence for a session that began at since.

        There is nothing to retrieve for an entity, which is read when asked for.
        """
        self.cancel()
        if self._request is None:
            return
        self._on_event = on_event
        self._active = True
        elapsed = (dt_util.utcnow() - since).total_seconds()
        self._start_sequence(1, max(DIRECT_READ_FIRST_DELAY_S - elapsed, 0))

    def begin_charging(self) -> None:
        """Start the second sequence with the first charging phase.

        It replaces a first sequence that is still under way, and does not
        run at all once a value was read or the second sequence already ran.
        """
        if (
            self._request is None
            or not self._active
            or self._value is not None
            or self._sequence != 1
        ):
            return
        self._halt()
        self._start_sequence(2, 0)

    def stop(self) -> None:
        """Stop reading and keep what was read."""
        self._halt()
        self._active = False

    def cancel(self) -> None:
        """Stop reading and forget what was read."""
        self.stop()
        self._on_event = None
        self._sequence = 0
        self._attempts = 0
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

    def _start_sequence(self, sequence: int, delay_s: float) -> None:
        """Begin a sequence whose first read comes after delay_s."""
        self._sequence = sequence
        self._attempts = 0
        self._reading = True
        self._schedule(delay_s)

    def _halt(self) -> None:
        """Cancel the pending read and one that is under way."""
        self._generation += 1
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        if self._task is not None and self._task is not asyncio.current_task():
            self._task.cancel()
        self._task = None
        self._reading = False

    def _schedule(self, delay_s: float) -> None:
        """Run the next read after delay_s; a read that is due now starts at the next turn."""
        if delay_s <= 0:
            self._start_read()
        else:
            self._unsub = async_call_later(self._hass, delay_s, self._on_timer)

    @callback
    def _on_timer(self, _now: datetime) -> None:
        """Start the read that is due."""
        self._unsub = None
        self._start_read()

    def _start_read(self) -> None:
        """Start one read as a task of its own, never inside the caller."""
        self._task = self._hass.async_create_task(self._async_read(), eager_start=False)

    def _emit(self, event: ReadEvent) -> None:
        """Tell the owner what happened."""
        if self._on_event is not None:
            self._on_event(event)

    async def _async_read(self) -> None:
        """Read the register once and either finish, schedule a further read or give up."""
        assert self._request is not None
        generation = self._generation
        endpoint, spec = self._request
        try:
            raw = await direct_read.async_read_register(self._hass, endpoint, spec)
        except Exception:
            _LOGGER.exception("Reading the identification from the wallbox raised an error")
            raw = None
        if generation != self._generation:
            return

        self._attempts += 1
        value: str | None = None
        failure = READ_FAILURE_UNREACHABLE
        if raw == 0:
            failure = READ_FAILURE_INVALID_VALUE
        elif raw is not None:
            text = direct_read.format_value(raw, spec.output)
            value = normalize_card_uid(text) if text else None
            if not value or value in INVALID_CARD_UIDS:
                value, failure = None, READ_FAILURE_INVALID_VALUE

        if value is not None:
            self._value = value
            self._failure = None
            self._reading = False
            self._emit(ReadEvent.VALUE)
        elif self._attempts < DIRECT_READ_MAX_READS:
            self._schedule(DIRECT_READ_INTERVAL_S)
            self._emit(ReadEvent.PROGRESS)
        else:
            self._reading = False
            if self._sequence == 2:
                self._failure = failure
                self._emit(ReadEvent.EXHAUSTED)
            else:
                self._emit(ReadEvent.PROGRESS)
