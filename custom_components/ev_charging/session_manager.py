"""Session capture at the wallbox: state machine, phases, counters, identification."""

from __future__ import annotations

import logging
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.event import (
    async_call_later,
    async_track_entity_registry_updated_event,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from . import allocation, problems, resolver
from .const import (
    ACTIVE_VEHICLE_GUEST,
    ACTIVE_VEHICLE_NONE,
    ACTIVE_VEHICLE_UNRESOLVED,
    CHARGE_STATE_CHARGING,
    CHARGE_STATE_DEFAULT,
    CHARGE_TYPE_SOURCE_WALLBOX_CONFIG,
    COUNTER_CHECK_INTERVAL_S,
    COUNTER_DEVIATION_TOLERANCE,
    COUNTER_SESSION,
    COUNTER_TOTAL,
    DISTANCE_UNIT_FACTORS_TO_KM,
    ENERGY_UNIT_FACTORS_TO_KWH,
    ERROR_CLASS_ERROR,
    ERROR_CLASS_OK,
    ERROR_DEBOUNCE_S,
    FINAL_VALUES_GRACE_S,
    GRID_POWER_WINDOW_S,
    IDENTIFICATION_MAX_AGE_MIN,
    IDENTIFICATION_SOURCE_UNRESOLVED,
    IDENTIFICATION_SOURCE_VEHICLE_API,
    INVALID_CARD_UIDS,
    LIVE_PUSH_INTERVAL_S,
    LOCATION_HOME,
    MAX_PHASES,
    MIN_PAUSE_MIN,
    MIN_PLAUSIBILITY_INTERVAL_S,
    PERSIST_INTERVAL_S,
    PLUG_STATE_CONNECTED,
    PLUG_STATE_NOT_CONNECTED,
    POWER_TOLERANCE_FACTOR,
    POWER_UNIT_FACTORS_TO_KW,
    ROLE_CHARGE_POWER,
    ROLE_CHARGE_STATE,
    ROLE_ENERGY_SESSION,
    ROLE_ENERGY_TOTAL,
    ROLE_ERROR,
    ROLE_GRID_EXPORT,
    ROLE_GRID_IMPORT,
    ROLE_GRID_POWER,
    ROLE_ODOMETER,
    ROLE_PLUG_STATE,
    ROLE_PRICE_FEED_IN,
    ROLE_PRICE_GRID,
    ROLE_SOC,
    ROLE_SOC_TARGET,
    SESSION_STATE_AWAITING_FINAL,
    SESSION_STATE_CANDIDATE,
    SESSION_STATE_CHARGING,
    SESSION_STATE_ERROR,
    SESSION_STATE_IDLE,
    SESSION_STATE_PAUSED,
    SESSION_STATUS_COMPLETE,
    SESSION_STATUS_FLAGGED,
    SESSION_STATUS_FOLLOWUP_OPEN,
    SESSION_TIMEOUT_H,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TRACKER_STATE_HOME,
    TRACKER_STATE_NOT_HOME,
)
from .mappings import DeviceMapping
from .models import (
    EntityRole,
    HubSettings,
    Phase,
    Session,
    Vehicle,
    Wallbox,
    derive_energy_kwh,
    merge_shortest_pauses,
    normalize_card_uid,
)
from .store import RuntimeStore, SessionYearStore, async_list_session_years

_LOGGER = logging.getLogger(__name__)

# States in which a session exists.
_SESSION_STATES = (
    SESSION_STATE_CANDIDATE,
    SESSION_STATE_CHARGING,
    SESSION_STATE_PAUSED,
    SESSION_STATE_ERROR,
    SESSION_STATE_AWAITING_FINAL,
)
# States in which the connection to the vehicle is still expected to hold.
_RUNNING_STATES = (SESSION_STATE_CHARGING, SESSION_STATE_PAUSED, SESSION_STATE_ERROR)


class StepKind(StrEnum):
    """How a counter reading relates to the previous one."""

    NORMAL = "normal"
    RESET = "reset"
    IMPLAUSIBLE = "implausible"


@dataclass(frozen=True, slots=True)
class CounterStep:
    """The energy to accumulate for one counter reading, and how it came about."""

    kind: StepKind
    delta_kwh: float


def counter_step(
    previous: float, current: float, *, max_power_kw: float, elapsed_s: float
) -> CounterStep:
    """Return the energy to accumulate when a counter moves from previous to current.

    A decrease means the counter was reset, and the new reading counts in full.
    An increase larger than the wallbox could have delivered in the elapsed
    time, with its power tolerance, is not accumulated at all: the counter
    changed its scale or was replaced, and treating the jump as energy would
    produce plausible but wrong numbers.
    """
    delta = current - previous
    reset = delta < 0
    increment = current if reset else delta
    interval_h = max(elapsed_s, MIN_PLAUSIBILITY_INTERVAL_S) / 3600
    if increment > max_power_kw * POWER_TOLERANCE_FACTOR * interval_h:
        return CounterStep(StepKind.IMPLAUSIBLE, 0.0)
    return CounterStep(StepKind.RESET if reset else StepKind.NORMAL, increment)


@dataclass(frozen=True, slots=True)
class Identification:
    """The outcome of the vehicle identification cascade."""

    source: str
    vehicle_id: str | None = None
    card_uid: str | None = None
    card_label: str | None = None
    conflict: bool = False
    unknown_card: bool = False


def identify(
    reported_card: str | None,
    vehicles: Sequence[Vehicle],
    home_vehicle_ids: Collection[str],
) -> Identification:
    """Decide which vehicle a session belongs to, from positive evidence only.

    reported_card is the card value the wallbox reported, normalized, valid
    and recent enough, or None. home_vehicle_ids are the active vehicles that
    identify themselves through their own integration and report being at
    home. A vehicle is never chosen because the others are absent.

    A reported value matches a stored card when it forms the end of the full
    identifier. A value that matches several cards is no match. A valid value
    that matches no card at all stops the cascade: the card is someone else's.
    """
    card_uid: str | None = None
    if reported_card is not None:
        matches = [
            (vehicle, card)
            for vehicle in vehicles
            if vehicle.active
            for card in vehicle.cards
            if card.active and card.uid.endswith(reported_card)
        ]
        if len(matches) == 1:
            vehicle, card = matches[0]
            conflict = len(home_vehicle_ids) == 1 and vehicle.id not in home_vehicle_ids
            return Identification(
                source=card.type,
                vehicle_id=vehicle.id,
                card_uid=card.uid,
                card_label=card.label,
                conflict=conflict,
            )
        card_uid = reported_card
        if not matches:
            return Identification(
                IDENTIFICATION_SOURCE_UNRESOLVED, card_uid=card_uid, unknown_card=True
            )

    if len(home_vehicle_ids) == 1:
        (vehicle_id,) = home_vehicle_ids
        return Identification(
            IDENTIFICATION_SOURCE_VEHICLE_API, vehicle_id=vehicle_id, card_uid=card_uid
        )
    return Identification(IDENTIFICATION_SOURCE_UNRESOLVED, card_uid=card_uid)


def energy_raw_kwh(
    soc_start: float | None, soc_end: float | None, capacity_kwh: float | None
) -> float | None:
    """Return the energy implied by the change of the state of charge, without any factor."""
    if soc_start is None or soc_end is None or capacity_kwh is None:
        return None
    return (soc_end - soc_start) / 100 * capacity_kwh


def _iso(moment: datetime) -> str:
    """Format a moment as local ISO 8601 with offset, to the second."""
    return dt_util.as_local(moment).replace(microsecond=0).isoformat()


def _parse(value: str | None) -> datetime | None:
    """Parse a stored ISO timestamp."""
    return dt_util.parse_datetime(value) if value else None


@dataclass
class _Counter:
    """Accumulation state of one energy counter."""

    value: float | None = None
    timestamp: datetime | None = None
    start_value: float | None = None
    accumulated: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the runtime store."""
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "start_value": self.start_value,
            "accumulated": self.accumulated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> _Counter:
        """Deserialize from the runtime store."""
        return cls(
            value=data.get("value"),
            timestamp=_parse(data.get("timestamp")),
            start_value=data.get("start_value"),
            accumulated=data.get("accumulated", 0.0),
        )


@dataclass
class RunningSession:
    """The session in progress. Serialized to the runtime store at every transition."""

    start: datetime
    state: str = SESSION_STATE_CANDIDATE
    phases: list[Phase] = field(default_factory=list)
    pause_since: datetime | None = None
    plug_end: datetime | None = None
    counters: dict[str, _Counter] = field(default_factory=dict)
    authoritative: str = COUNTER_TOTAL
    grid_kwh: float = 0.0
    solar_kwh: float = 0.0
    cost: float = 0.0
    unallocated_kwh: float = 0.0
    cost_started: bool = False
    cost_incomplete: bool = False
    last_share: float | None = None
    gap_pending: bool = False
    check_snapshot: dict[str, float] = field(default_factory=dict)
    stalled_checks: int = 0
    identification_decided: bool = False
    identification_source: str = IDENTIFICATION_SOURCE_UNRESOLVED
    vehicle_id: str | None = None
    card_uid: str | None = None
    card_label: str | None = None
    identification_conflict: bool = False
    unknown_card: bool = False
    location_conflict: bool = False
    soc_start: float | None = None
    odometer_km: float | None = None
    charge_error: bool = False
    flagged: bool = False
    plug_last_valid: datetime | None = None
    plug_unavailable_since: datetime | None = None

    def open_phase(self) -> Phase | None:
        """Return the phase that is still open, if any."""
        if self.phases and self.phases[-1].end is None:
            return self.phases[-1]
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the runtime store."""
        return {
            "start": self.start.isoformat(),
            "state": self.state,
            "phases": [phase.to_dict() for phase in self.phases],
            "pause_since": self.pause_since.isoformat() if self.pause_since else None,
            "plug_end": self.plug_end.isoformat() if self.plug_end else None,
            "counters": {kind: counter.to_dict() for kind, counter in self.counters.items()},
            "authoritative": self.authoritative,
            "grid_kwh": self.grid_kwh,
            "solar_kwh": self.solar_kwh,
            "cost": self.cost,
            "unallocated_kwh": self.unallocated_kwh,
            "cost_started": self.cost_started,
            "cost_incomplete": self.cost_incomplete,
            "last_share": self.last_share,
            "gap_pending": self.gap_pending,
            "check_snapshot": self.check_snapshot,
            "stalled_checks": self.stalled_checks,
            "identification_decided": self.identification_decided,
            "identification_source": self.identification_source,
            "vehicle_id": self.vehicle_id,
            "card_uid": self.card_uid,
            "card_label": self.card_label,
            "identification_conflict": self.identification_conflict,
            "unknown_card": self.unknown_card,
            "location_conflict": self.location_conflict,
            "soc_start": self.soc_start,
            "odometer_km": self.odometer_km,
            "charge_error": self.charge_error,
            "flagged": self.flagged,
            "plug_last_valid": self.plug_last_valid.isoformat() if self.plug_last_valid else None,
            "plug_unavailable_since": (
                self.plug_unavailable_since.isoformat() if self.plug_unavailable_since else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunningSession:
        """Deserialize from the runtime store."""
        start = _parse(data["start"])
        if start is None:
            raise ValueError("stored session has an unreadable start")
        return cls(
            start=start,
            state=data.get("state", SESSION_STATE_CANDIDATE),
            phases=[Phase.from_dict(phase) for phase in data.get("phases", [])],
            pause_since=_parse(data.get("pause_since")),
            plug_end=_parse(data.get("plug_end")),
            counters={
                kind: _Counter.from_dict(counter)
                for kind, counter in data.get("counters", {}).items()
            },
            authoritative=data.get("authoritative", COUNTER_TOTAL),
            grid_kwh=data.get("grid_kwh", 0.0),
            solar_kwh=data.get("solar_kwh", 0.0),
            cost=data.get("cost", 0.0),
            unallocated_kwh=data.get("unallocated_kwh", 0.0),
            cost_started=data.get("cost_started", False),
            cost_incomplete=data.get("cost_incomplete", False),
            last_share=data.get("last_share"),
            gap_pending=data.get("gap_pending", False),
            check_snapshot=dict(data.get("check_snapshot", {})),
            stalled_checks=data.get("stalled_checks", 0),
            identification_decided=data.get("identification_decided", False),
            identification_source=data.get(
                "identification_source", IDENTIFICATION_SOURCE_UNRESOLVED
            ),
            vehicle_id=data.get("vehicle_id"),
            card_uid=data.get("card_uid"),
            card_label=data.get("card_label"),
            identification_conflict=data.get("identification_conflict", False),
            unknown_card=data.get("unknown_card", False),
            location_conflict=data.get("location_conflict", False),
            soc_start=data.get("soc_start"),
            odometer_km=data.get("odometer_km"),
            charge_error=data.get("charge_error", False),
            flagged=data.get("flagged", False),
            plug_last_valid=_parse(data.get("plug_last_valid")),
            plug_unavailable_since=_parse(data.get("plug_unavailable_since")),
        )


@dataclass(frozen=True, slots=True)
class VehicleContext:
    """A vehicle together with what is needed to read and classify its entities."""

    vehicle: Vehicle
    subentry_id: str
    title: str
    mapping: DeviceMapping | None


@dataclass(frozen=True, slots=True)
class WallboxSnapshot:
    """What the entities publish. Rebuilt at every state change and at the publish interval."""

    state: str
    session_active: bool
    active_vehicle: str
    session_start: datetime | None
    cost: float | None
    energy_grid_kwh: float | None
    energy_solar_kwh: float | None
    effective_price: float | None
    grid_share_pct: float | None
    soc_start: float | None
    odometer_start: float | None
    duration_net_min: float | None
    vehicle_soc: float | None
    vehicle_soc_target: float | None
    vehicle_charge_state: str | None
    vehicle_charge_end: datetime | None
    open_followups: int


class SessionManager:
    """Captures charging sessions at the one wallbox.

    Reads the resolved source entities, runs the session state machine and
    publishes the result. Nothing here writes to a device or calls a service.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Prepare the manager for the hub entry; async_setup wires it up."""
        self._hass = hass
        self._entry = entry
        self._settings = HubSettings.from_dict(entry.data)
        self._wallbox_subentry: ConfigSubentry | None = None
        self.wallbox: Wallbox | None = None
        self._wallbox_mapping: DeviceMapping | None = None
        self._vehicles: dict[str, VehicleContext] = {}

        self._session: RunningSession | None = None
        self._timers: dict[str, CALLBACK_TYPE] = {}
        self._listeners: list[CALLBACK_TYPE] = []
        self._live_listeners: list[CALLBACK_TYPE] = []
        self._unsubs: list[CALLBACK_TYPE] = []
        self._source_unsubs: list[CALLBACK_TYPE] = []
        self._watch: dict[str, list[Callable[[State | None], None]]] = {}

        self._power_kw: float | None = None
        self._grid_average = allocation.MovingAverage(GRID_POWER_WINDOW_S)
        self._price_grid: float | None = None
        self._price_feed_in: float | None = None
        self._last_share: float | None = None
        self._plug_class: str | None = None
        self._plug_usable = False
        self._error_class: str | None = None
        self._vehicle_charge_class: dict[str, str | None] = {}
        self._units_seen: dict[str, str | None] = {}
        self._counter_detection: dict[str, str] | None = None
        self._open_followups = 0
        self._finalizing = False
        self.snapshot = self._build_snapshot()

    # ------------------------------------------------------------------ setup

    @property
    def settings(self) -> HubSettings:
        """Return the global settings."""
        return self._settings

    @property
    def wallbox_subentry_id(self) -> str | None:
        """Return the id of the wallbox subentry."""
        return self._wallbox_subentry.subentry_id if self._wallbox_subentry else None

    async def async_setup(self) -> bool:
        """Load the configuration and the stored state and start observing.

        Returns False if there is no wallbox to observe.
        """
        wallbox_subentry = next(
            (
                subentry
                for subentry in self._entry.subentries.values()
                if subentry.subentry_type == SUBENTRY_TYPE_WALLBOX
            ),
            None,
        )
        if wallbox_subentry is None:
            return False
        self._wallbox_subentry = wallbox_subentry
        self.wallbox = Wallbox.from_dict(wallbox_subentry.data)
        self._wallbox_mapping = await resolver.async_get_mapping(
            self._hass, self.wallbox.mapping_id
        )
        for subentry in self._entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_VEHICLE:
                vehicle = Vehicle.from_dict(subentry.data)
                self._vehicles[vehicle.id] = VehicleContext(
                    vehicle=vehicle,
                    subentry_id=subentry.subentry_id,
                    title=subentry.title,
                    mapping=await resolver.async_get_mapping(self._hass, vehicle.mapping_id),
                )

        stored = await RuntimeStore(self._hass).async_load()
        self._counter_detection = stored.get("counter_detection")
        if stored.get("session"):
            try:
                self._session = RunningSession.from_dict(stored["session"])
            except KeyError, ValueError:
                _LOGGER.exception("The stored session could not be restored and is dropped")
        self._open_followups = await self._async_count_followups()

        self._subscribe_sources()
        self._unsubs.append(
            async_track_time_interval(
                self._hass,
                self._on_publish_tick,
                timedelta(seconds=self._settings.update_interval_s),
            )
        )
        self._unsubs.append(
            async_track_time_interval(
                self._hass, self._on_persist_tick, timedelta(seconds=PERSIST_INTERVAL_S)
            )
        )

        self._restore_session_timers()
        self._apply_current_states()
        self._publish()
        return True

    async def async_unload(self) -> None:
        """Stop observing and cancel every timer. The running session stays in the store."""
        for unsub in [*self._unsubs, *self._source_unsubs]:
            unsub()
        self._unsubs.clear()
        self._source_unsubs.clear()
        for name in list(self._timers):
            self._cancel_timer(name)
        self._listeners.clear()
        self._live_listeners.clear()
        if self._session is not None:
            await self._async_persist()

    def _watch_role(self, role: EntityRole | None, handler: Callable[[State | None], None]) -> None:
        """Register a handler for the entity a role currently resolves to."""
        entity_id = resolver.resolve_entity_id(self._hass, role)
        if entity_id is not None:
            self._watch.setdefault(entity_id, []).append(handler)

    def _subscribe_sources(self) -> None:
        """Observe every source entity that matters, and follow renames.

        The order of registration is the order in which the present states
        are applied at startup: plug and error before the counters and the
        power, so a restored session is judged against the connector first.
        """
        for unsub in self._source_unsubs:
            unsub()
        self._source_unsubs = []
        self._watch = {}
        assert self.wallbox is not None
        wallbox = self.wallbox
        settings = self._settings

        self._watch_role(wallbox.plug_state, self._on_plug)
        self._watch_role(wallbox.error, self._on_error)
        self._watch_role(wallbox.identification, self._on_identification_value)
        self._watch_role(settings.grid_power, self._on_grid_power)
        self._watch_role(settings.grid_import, self._on_grid_pair)
        self._watch_role(settings.grid_export, self._on_grid_pair)
        self._watch_role(settings.price_grid, self._on_price_grid)
        self._watch_role(settings.price_feed_in, self._on_price_feed_in)
        for context in self._vehicles.values():
            vehicle = context.vehicle
            if not vehicle.active:
                continue
            self._watch_role(
                vehicle.charge_state, lambda s, c=context: self._on_vehicle_charge_state(c, s)
            )
            self._watch_role(vehicle.location, lambda _s: self._on_vehicle_location())
            for role in (vehicle.soc, vehicle.soc_target, vehicle.odometer, vehicle.charge_end):
                self._watch_role(role, lambda _s: self._touch_live())
        self._watch_role(wallbox.energy_total, lambda s: self._on_counter(COUNTER_TOTAL, s))
        self._watch_role(wallbox.energy_session, lambda s: self._on_counter(COUNTER_SESSION, s))
        self._watch_role(wallbox.charge_power, self._on_power)

        if self._watch:
            self._source_unsubs.append(
                async_track_state_change_event(self._hass, list(self._watch), self._on_state_event)
            )
            self._source_unsubs.append(
                async_track_entity_registry_updated_event(
                    self._hass, list(self._watch), self._on_registry_event
                )
            )

    @callback
    def _on_registry_event(self, event: Event[Any]) -> None:
        """Follow a renamed source entity."""
        if event.data.get("action") == "update" and "old_entity_id" in event.data:
            self._subscribe_sources()

    @callback
    def _on_state_event(self, event: Event[EventStateChangedData]) -> None:
        """Dispatch a state change to the handlers of that entity."""
        state = event.data["new_state"]
        for handler in self._watch.get(event.data["entity_id"], ()):
            handler(state)

    def _apply_current_states(self) -> None:
        """Feed the present state of every source to the handlers, as after a change."""
        for entity_id, handlers in list(self._watch.items()):
            state = self._hass.states.get(entity_id)
            for handler in handlers:
                handler(state)

    # ----------------------------------------------------------------- helpers

    def _now(self) -> datetime:
        """Return the current time."""
        return dt_util.utcnow()

    def _set_timer(self, name: str, delay_s: float, action: Callable[..., Any]) -> None:
        """Start or restart a named one-shot timer."""
        self._cancel_timer(name)
        self._timers[name] = async_call_later(self._hass, max(delay_s, 0), action)

    def _cancel_timer(self, name: str) -> None:
        """Cancel a named timer if it is running."""
        unsub = self._timers.pop(name, None)
        if unsub is not None:
            unsub()

    def _check_unit(self, key: str, role: EntityRole | None, state: State | None) -> None:
        """Raise the unit-changed repair issue when a numeric source reports a new unit."""
        if role is None or state is None:
            return
        unit = state.attributes.get("unit_of_measurement")
        if self._units_seen.get(key) == unit:
            return
        self._units_seen[key] = unit
        subentry = self._wallbox_subentry
        assert subentry is not None
        subentry_id = self._entry.entry_id if key.startswith("hub_") else subentry.subentry_id
        title = self._entry.title if key.startswith("hub_") else subentry.title
        role_name = key.removeprefix("hub_")
        resolver.check_role_unit(
            self._hass,
            role,
            issue_id=problems.role_unit_changed_issue_id(subentry_id, role_name),
            translation_key="role_unit_changed",
            translation_placeholders={"role": role_name, "subentry_title": title},
        )

    # ------------------------------------------------------- source handlers

    @callback
    def _on_power(self, state: State | None) -> None:
        """Handle a new charging power reading."""
        assert self.wallbox is not None
        self._check_unit(ROLE_CHARGE_POWER, self.wallbox.charge_power, state)
        self._power_kw = resolver.read_number(
            state, self.wallbox.charge_power, POWER_UNIT_FACTORS_TO_KW
        )
        if self._power_kw is not None:
            self._track_power_max(self._power_kw)
            self._evaluate_power(self._now())
        self._touch_live()

    def _power_active(self) -> bool:
        """Whether the charging power is above the session threshold."""
        assert self.wallbox is not None
        return self._power_kw is not None and self._power_kw > self.wallbox.power_threshold_kw

    def _track_power_max(self, power_kw: float) -> None:
        """Keep the highest power seen in the open phase."""
        session = self._session
        if session is None:
            return
        phase = session.open_phase()
        if phase is not None and (phase.power_max_kw is None or power_kw > phase.power_max_kw):
            session.phases[-1] = replace(phase, power_max_kw=power_kw)

    def _evaluate_power(self, now: datetime) -> None:
        """Move the state machine according to the charging power."""
        session = self._session
        active = self._power_active()
        if session is None:
            if active and self._plug_class != PLUG_STATE_NOT_CONNECTED:
                self._start_candidate(now)
            return
        if session.state == SESSION_STATE_CANDIDATE:
            if not active:
                self._discard_candidate()
        elif session.state == SESSION_STATE_CHARGING:
            if not active:
                self._pause(now)
        elif session.state in (SESSION_STATE_PAUSED, SESSION_STATE_ERROR) and active:
            self._resume(now)

    @callback
    def _on_plug(self, state: State | None) -> None:
        """Handle a new plug state of the wallbox."""
        assert self.wallbox is not None
        now = self._now()
        raw = resolver.usable_state(state)
        session = self._session
        self._plug_usable = raw is not None
        if raw is None:
            if session is not None and session.state in _SESSION_STATES:
                self._plug_unavailable(session, now)
            return
        if session is not None:
            session.plug_last_valid = now
            session.plug_unavailable_since = None
            self._cancel_timer("stale")
        mapping = (
            self._wallbox_mapping.role_values(ROLE_PLUG_STATE) if self._wallbox_mapping else {}
        )
        klass, found = resolver.classify_with_neutral(
            raw, mapping, default=PLUG_STATE_CONNECTED, last_class=self._plug_class
        )
        self._raise_unknown_value(found, self._wallbox_subentry, ROLE_PLUG_STATE, raw)
        if klass is not None:
            self._plug_class = klass
        if klass == PLUG_STATE_NOT_CONNECTED and session is not None:
            self._unplug(now)
        self._touch_live()

    def _raise_unknown_value(
        self, found: bool, subentry: ConfigSubentry | None, role_name: str, raw: str
    ) -> None:
        """Create or clear the repair issue for a raw value the mapping does not know."""
        if subentry is None:
            return
        problems.check_unknown_mapping_value(
            self._hass,
            found=found,
            subentry_id=subentry.subentry_id,
            subentry_title=subentry.title,
            role_name=role_name,
            raw_value=raw,
        )

    def _plug_unavailable(self, session: RunningSession, now: datetime) -> None:
        """Note that the plug state is not usable and start the timeout for a lasting outage."""
        if session.plug_unavailable_since is None:
            session.plug_unavailable_since = now
        if "stale" not in self._timers:
            elapsed = (now - session.plug_unavailable_since).total_seconds()
            self._set_timer("stale", SESSION_TIMEOUT_H * 3600 - elapsed, self._on_stale_timer)

    @callback
    def _on_error(self, state: State | None) -> None:
        """Handle a new value of the wallbox error role."""
        assert self.wallbox is not None and self.wallbox.error is not None
        raw = resolver.usable_state(state)
        if raw is None or state is None:
            return
        mapping = self._wallbox_mapping.role_values(ROLE_ERROR) if self._wallbox_mapping else {}
        previous = self._error_class
        if mapping:
            klass, found = resolver.classify_with_neutral(
                raw, mapping, default=ERROR_CLASS_OK, last_class=previous
            )
            self._raise_unknown_value(found, self._wallbox_subentry, ROLE_ERROR, raw)
        elif state.domain == "binary_sensor" and raw in ("on", "off"):
            klass = ERROR_CLASS_ERROR if raw == "on" else ERROR_CLASS_OK
        else:
            klass = previous
        self._error_class = klass
        session = self._session
        if klass == ERROR_CLASS_ERROR and previous != ERROR_CLASS_ERROR:
            if session is not None and session.state in (
                SESSION_STATE_CHARGING,
                SESSION_STATE_PAUSED,
            ):
                self._set_timer("error", ERROR_DEBOUNCE_S, self._on_error_timer)
        elif klass != ERROR_CLASS_ERROR:
            self._cancel_timer("error")
            if session is not None and session.state == SESSION_STATE_ERROR:
                self._leave_error(self._now())
        self._touch_live()

    @callback
    def _on_identification_value(self, state: State | None) -> None:
        """Note a change of the reported card during a session; the first value stands."""
        session = self._session
        if session is not None and session.identification_decided:
            _LOGGER.debug("The reported card changed during a session and is ignored")

    @callback
    def _on_counter(self, kind: str, state: State | None) -> None:
        """Handle a new energy counter reading and accumulate it."""
        assert self.wallbox is not None
        role = self.wallbox.energy_total if kind == COUNTER_TOTAL else self.wallbox.energy_session
        self._check_unit(
            ROLE_ENERGY_TOTAL if kind == COUNTER_TOTAL else ROLE_ENERGY_SESSION, role, state
        )
        value = resolver.read_number(state, role, ENERGY_UNIT_FACTORS_TO_KWH)
        session = self._session
        if value is None or session is None:
            return
        now = self._now()
        counter = session.counters.setdefault(kind, _Counter())
        if counter.value is None or counter.timestamp is None:
            counter.value, counter.timestamp, counter.start_value = value, now, value
            return
        step = counter_step(
            counter.value,
            value,
            max_power_kw=self.wallbox.max_power_kw,
            elapsed_s=(now - counter.timestamp).total_seconds(),
        )
        counter.value, counter.timestamp = value, now
        if step.kind is StepKind.IMPLAUSIBLE:
            session.flagged = True
            _LOGGER.warning(
                "An energy counter jumped by more than the wallbox can deliver; "
                "the step is not counted and the session is flagged"
            )
        counter.accumulated += step.delta_kwh
        if kind == session.authoritative:
            if session.gap_pending:
                self._add_unallocated(session, step.delta_kwh)
                session.gap_pending = False
            elif step.delta_kwh > 0:
                self._allocate(session, step.delta_kwh, now)
        self._touch_live()

    @callback
    def _on_grid_power(self, state: State | None) -> None:
        """Handle a new grid balance reading."""
        role = self._settings.grid_power
        self._check_unit(f"hub_{ROLE_GRID_POWER}", role, state)
        value = resolver.read_number(state, role, POWER_UNIT_FACTORS_TO_KW)
        if value is None:
            self._grid_average.reset()
        else:
            sign = -1 if self._settings.grid_power_inverted else 1
            self._grid_average.add(self._now().timestamp(), sign * value)
        self._touch_live()

    @callback
    def _on_grid_pair(self, state: State | None) -> None:
        """Handle a reading of the import or export entity of the grid pair."""
        settings = self._settings
        for role_name, role in (
            (ROLE_GRID_IMPORT, settings.grid_import),
            (ROLE_GRID_EXPORT, settings.grid_export),
        ):
            if role is not None:
                entity_id = resolver.resolve_entity_id(self._hass, role)
                self._check_unit(
                    f"hub_{role_name}",
                    role,
                    self._hass.states.get(entity_id) if entity_id else None,
                )
        imported = self._read_hub_power(settings.grid_import)
        exported = self._read_hub_power(settings.grid_export)
        if imported is None or exported is None:
            self._grid_average.reset()
        else:
            self._grid_average.add(self._now().timestamp(), imported - exported)
        self._touch_live()

    def _read_hub_power(self, role: EntityRole | None) -> float | None:
        """Read the current power of a hub role in kW."""
        entity_id = resolver.resolve_entity_id(self._hass, role)
        if entity_id is None:
            return None
        return resolver.read_number(
            self._hass.states.get(entity_id), role, POWER_UNIT_FACTORS_TO_KW
        )

    @callback
    def _on_price_grid(self, state: State | None) -> None:
        """Handle a new grid price. An unusable reading keeps the last valid price."""
        self._check_unit(f"hub_{ROLE_PRICE_GRID}", self._settings.price_grid, state)
        value = resolver.read_number(state, self._settings.price_grid, None)
        if value is not None:
            self._price_grid = value
        self._touch_live()

    @callback
    def _on_price_feed_in(self, state: State | None) -> None:
        """Handle a new feed-in price. An unusable reading keeps the last valid price."""
        self._check_unit(f"hub_{ROLE_PRICE_FEED_IN}", self._settings.price_feed_in, state)
        value = resolver.read_number(state, self._settings.price_feed_in, None)
        if value is not None:
            self._price_feed_in = value
        self._touch_live()

    @callback
    def _on_vehicle_charge_state(self, context: VehicleContext, state: State | None) -> None:
        """Classify a vehicle's charge state and try to resolve an unassigned session."""
        raw = resolver.usable_state(state)
        if raw is None:
            return
        mapping = context.mapping.role_values(ROLE_CHARGE_STATE) if context.mapping else {}
        klass, found = resolver.classify_with_neutral(
            raw,
            mapping,
            default=CHARGE_STATE_DEFAULT,
            last_class=self._vehicle_charge_class.get(context.vehicle.id),
        )
        problems.check_unknown_mapping_value(
            self._hass,
            found=found,
            subentry_id=context.subentry_id,
            subentry_title=context.title,
            role_name=ROLE_CHARGE_STATE,
            raw_value=raw,
        )
        self._vehicle_charge_class[context.vehicle.id] = klass
        self._resolve_late()
        self._touch_live()

    @callback
    def _on_vehicle_location(self) -> None:
        """Re-check the location of the assigned vehicle."""
        self._evaluate_location_conflict()
        self._touch_live()

    # ----------------------------------------------------- state transitions

    def _start_candidate(self, now: datetime) -> None:
        """Create the candidate at the moment the power first exceeds the threshold."""
        assert self.wallbox is not None
        session = RunningSession(start=now, state=SESSION_STATE_CANDIDATE)
        session.authoritative = self._default_authoritative()
        session.last_share = self._last_share
        for kind, role in (
            (COUNTER_TOTAL, self.wallbox.energy_total),
            (COUNTER_SESSION, self.wallbox.energy_session),
        ):
            if role is None:
                continue
            counter = _Counter()
            entity_id = resolver.resolve_entity_id(self._hass, role)
            value = resolver.read_number(
                self._hass.states.get(entity_id) if entity_id else None,
                role,
                ENERGY_UNIT_FACTORS_TO_KWH,
            )
            if value is not None:
                counter.value, counter.timestamp, counter.start_value = value, now, value
            session.counters[kind] = counter
        session.phases.append(Phase(start=_iso(now), power_max_kw=self._power_kw))
        session.plug_last_valid = now
        self._session = session
        if not self._plug_usable:
            self._plug_unavailable(session, now)
        self._start_counter_check()
        self._enter(SESSION_STATE_CANDIDATE)

        if self.wallbox.start_debounce_s == 0:
            self._confirm_candidate(now)
        else:
            self._set_timer("debounce", self.wallbox.start_debounce_s, self._on_debounce_timer)
        self._schedule_identification()

    def _start_counter_check(self) -> None:
        """Watch the energy counters while a session runs."""
        self._cancel_timer("counter_check")
        self._timers["counter_check"] = async_track_time_interval(
            self._hass, self._on_counter_check, timedelta(seconds=COUNTER_CHECK_INTERVAL_S)
        )

    def _clear_session_timers(self) -> None:
        """Cancel every timer that belongs to a session."""
        for name in (
            "debounce",
            "identification",
            "pause",
            "error",
            "final",
            "stale",
            "counter_check",
        ):
            self._cancel_timer(name)

    def _default_authoritative(self) -> str:
        """Return the counter that carries the energy, from the stored detection or the setup."""
        assert self.wallbox is not None
        detected = self._counter_detection
        if detected and detected.get("key") == self._counter_key():
            return detected["authoritative"]
        return COUNTER_TOTAL if self.wallbox.energy_total is not None else COUNTER_SESSION

    def _counter_key(self) -> str:
        """Identify the current counter assignment, so a stored detection lapses when it changes."""
        assert self.wallbox is not None

        def ref(role: EntityRole | None) -> str:
            return (role.registry_entry_id or role.entity_id) if role else "-"

        return f"{ref(self.wallbox.energy_total)}|{ref(self.wallbox.energy_session)}"

    def _enter(self, state: str) -> None:
        """Record a new state, persist it and publish it at once."""
        assert self._session is not None
        self._session.state = state
        self._persist()
        self._publish()

    @callback
    def _on_debounce_timer(self, _now: datetime) -> None:
        """Confirm the candidate once the debounce time has passed."""
        self._timers.pop("debounce", None)
        self._confirm_candidate(self._now())

    def _confirm_candidate(self, now: datetime) -> None:
        """Turn the candidate into a running session if the power still holds."""
        session = self._session
        if session is None or session.state != SESSION_STATE_CANDIDATE:
            return
        if not self._power_active():
            self._discard_candidate()
            return
        self._enter(SESSION_STATE_CHARGING)
        if self._error_class == ERROR_CLASS_ERROR:
            self._set_timer("error", ERROR_DEBOUNCE_S, self._on_error_timer)

    def _discard_candidate(self) -> None:
        """Drop a candidate that did not last."""
        self._clear_session_timers()
        self._session = None
        self._persist()
        self._publish()

    def _pause(self, now: datetime) -> None:
        """Note that no energy is taken up; the phase stays open for the minimum pause."""
        session = self._session
        assert session is not None
        session.pause_since = now
        self._set_timer("pause", MIN_PAUSE_MIN * 60, self._on_pause_timer)
        self._enter(SESSION_STATE_PAUSED)

    @callback
    def _on_pause_timer(self, _now: datetime) -> None:
        """Close the phase once the interruption reached the minimum pause."""
        self._timers.pop("pause", None)
        session = self._session
        if session is not None and session.state == SESSION_STATE_PAUSED and session.pause_since:
            self._close_phase(session, session.pause_since)
            self._persist()

    def _resume(self, now: datetime) -> None:
        """Take up charging again within the running session."""
        session = self._session
        assert session is not None
        self._cancel_timer("pause")
        if session.open_phase() is None:
            self._open_phase(session, now)
        session.pause_since = None
        self._enter(SESSION_STATE_CHARGING)

    def _open_phase(self, session: RunningSession, now: datetime) -> None:
        """Start a new phase, joining the shortest pauses first when the limit is reached."""
        if len(session.phases) >= MAX_PHASES:
            session.phases = list(merge_shortest_pauses(tuple(session.phases), MAX_PHASES - 1))
            session.flagged = True
        session.phases.append(Phase(start=_iso(now), power_max_kw=self._power_kw))

    def _close_phase(self, session: RunningSession, end: datetime) -> None:
        """Close the open phase at the given moment."""
        phase = session.open_phase()
        if phase is None:
            return
        start = _parse(phase.start)
        duration = max((end - start).total_seconds() / 60, 0.0) if start else 0.0
        energy = phase.energy_kwh
        session.phases[-1] = replace(
            phase,
            end=_iso(end),
            duration_min=duration,
            power_avg_kw=energy / (duration / 60) if energy is not None and duration > 0 else None,
        )

    @callback
    def _on_error_timer(self, _now: datetime) -> None:
        """Enter the error state once the reported error has held for the debounce time."""
        self._timers.pop("error", None)
        session = self._session
        if session is None or self._error_class != ERROR_CLASS_ERROR:
            return
        if session.state not in (SESSION_STATE_CHARGING, SESSION_STATE_PAUSED):
            return
        end = (
            session.pause_since
            if session.state == SESSION_STATE_PAUSED and session.pause_since
            else self._now()
        )
        self._cancel_timer("pause")
        self._close_phase(session, end)
        session.pause_since = None
        session.charge_error = True
        self._enter(SESSION_STATE_ERROR)

    def _leave_error(self, now: datetime) -> None:
        """Go back to charging or paused once the error is no longer reported."""
        session = self._session
        assert session is not None
        if self._power_active():
            self._resume(now)
            return
        session.pause_since = now
        self._enter(SESSION_STATE_PAUSED)

    def _unplug(self, now: datetime) -> None:
        """React to the vehicle being disconnected, the end of a session."""
        session = self._session
        assert session is not None and self.wallbox is not None
        if session.state == SESSION_STATE_AWAITING_FINAL:
            return
        if session.state == SESSION_STATE_CANDIDATE:
            self._discard_candidate()
            return
        for name in ("debounce", "pause", "error", "stale"):
            self._cancel_timer(name)
        end = (
            session.pause_since
            if session.state == SESSION_STATE_PAUSED and session.pause_since
            else now
        )
        self._close_phase(session, end)
        session.plug_end = now
        self._enter(SESSION_STATE_AWAITING_FINAL)
        self._set_timer("final", FINAL_VALUES_GRACE_S, self._async_on_final_timer)

    @callback
    def _on_stale_timer(self, _now: datetime) -> None:
        """Close the session after the plug state was unusable for the whole timeout."""
        self._timers.pop("stale", None)
        session = self._session
        if session is None or session.state not in _SESSION_STATES:
            return
        for name in ("debounce", "pause", "error", "final"):
            self._cancel_timer(name)
        end = session.plug_last_valid or session.start
        self._close_phase(session, end)
        session.plug_end = end
        session.flagged = True
        session.state = SESSION_STATE_AWAITING_FINAL
        self._persist()
        self._publish()
        self._hass.async_create_task(self._async_finalize(stale=True))

    async def _async_on_final_timer(self, _now: datetime) -> None:
        """Write the session once the wait for final values is over."""
        self._timers.pop("final", None)
        await self._async_finalize(stale=False)

    # ------------------------------------------------------------ allocation

    def _grid_configured(self) -> bool:
        """Whether a grid balance is configured, so the energy can be split."""
        settings = self._settings
        return settings.grid_power is not None or (
            settings.grid_import is not None and settings.grid_export is not None
        )

    def _current_share(self, now: datetime) -> float | None:
        """Return the grid share for an increment at this moment."""
        if not self._grid_configured():
            return 1.0
        average = self._grid_average.average(now.timestamp())
        if average is not None and self._power_kw is not None:
            share = allocation.grid_share(average, self._power_kw)
            if share is not None:
                self._last_share = share
                return share
        return self._last_share

    def _grid_price(self) -> float | None:
        """Return the price of grid energy, fixed or from the entity."""
        fixed = self._settings.price_grid_fixed
        return fixed if fixed is not None else self._price_grid

    def _solar_price(self) -> float | None:
        """Return the price at which solar energy is valued."""
        fixed = self._settings.price_feed_in_fixed
        feed_in = fixed if fixed is not None else self._price_feed_in
        return allocation.solar_price(self._settings.solar_valuation, feed_in)

    def _prices_configured(self) -> bool:
        """Whether a grid price is configured; without one no cost is determined."""
        settings = self._settings
        return settings.price_grid is not None or settings.price_grid_fixed is not None

    def _add_unallocated(self, session: RunningSession, delta_kwh: float) -> None:
        """Book energy that cannot be assigned to grid or solar."""
        session.unallocated_kwh += delta_kwh
        self._add_to_phase(session, energy=delta_kwh)

    def _allocate(self, session: RunningSession, delta_kwh: float, now: datetime) -> None:
        """Split an energy increment into grid and solar share and value it."""
        share = self._current_share(now)
        session.last_share = self._last_share
        if share is None:
            self._add_unallocated(session, delta_kwh)
            return
        result = allocation.allocate(delta_kwh, share, self._grid_price(), self._solar_price())
        session.grid_kwh += result.grid_kwh
        session.solar_kwh += result.solar_kwh
        cost = 0.0
        if self._prices_configured():
            if result.cost is None:
                session.cost_incomplete = True
            else:
                session.cost += result.cost
                session.cost_started = True
                cost = result.cost
        self._add_to_phase(
            session, energy=delta_kwh, grid=result.grid_kwh, solar=result.solar_kwh, cost=cost
        )

    def _add_to_phase(
        self,
        session: RunningSession,
        *,
        energy: float,
        grid: float = 0.0,
        solar: float = 0.0,
        cost: float = 0.0,
    ) -> None:
        """Add an increment to the open phase, or to the last one while none is open."""
        if not session.phases:
            return
        phase = session.phases[-1]
        session.phases[-1] = replace(
            phase,
            energy_kwh=(phase.energy_kwh or 0.0) + energy,
            energy_grid_kwh=(phase.energy_grid_kwh or 0.0) + grid,
            energy_solar_kwh=(phase.energy_solar_kwh or 0.0) + solar,
            cost=(phase.cost or 0.0) + cost,
        )

    @callback
    def _on_counter_check(self, _now: datetime) -> None:
        """Switch to the other energy counter when the authoritative one stands still."""
        session = self._session
        if session is None or len(session.counters) < 2:
            return
        current = {kind: counter.accumulated for kind, counter in session.counters.items()}
        if session.state != SESSION_STATE_CHARGING:
            session.check_snapshot, session.stalled_checks = current, 0
            return
        other = COUNTER_SESSION if session.authoritative == COUNTER_TOTAL else COUNTER_TOTAL
        previous = session.check_snapshot
        grew_authoritative = current[session.authoritative] > previous.get(session.authoritative, 0)
        grew_other = current[other] > previous.get(other, 0)
        session.check_snapshot = current
        if not grew_authoritative and grew_other:
            session.stalled_checks += 1
        else:
            session.stalled_checks = 0
        if session.stalled_checks >= 2:
            self._switch_counter(session, other)

    def _switch_counter(self, session: RunningSession, counter: str) -> None:
        """Make the other counter authoritative and remember that."""
        assert self._wallbox_subentry is not None
        session.authoritative = counter
        session.stalled_checks = 0
        assigned = session.grid_kwh + session.solar_kwh + session.unallocated_kwh
        session.unallocated_kwh += max(session.counters[counter].accumulated - assigned, 0.0)
        self._counter_detection = {"key": self._counter_key(), "authoritative": counter}
        problems.async_create_counter_switched_issue(
            self._hass,
            wallbox_id=self._wallbox_subentry.subentry_id,
            wallbox_title=self._wallbox_subentry.title,
            counter=f"energy_{counter}",
        )
        self._persist()

    # -------------------------------------------------------- identification

    def _schedule_identification(self) -> None:
        """Decide the vehicle once the identification window has passed."""
        assert self.wallbox is not None and self._session is not None
        window = self.wallbox.identification_window_s
        if window == 0:
            self._decide_identification()
            return
        remaining = window - (self._now() - self._session.start).total_seconds()
        self._set_timer("identification", remaining, self._on_identification_timer)

    @callback
    def _on_identification_timer(self, _now: datetime) -> None:
        """Decide the vehicle at the end of the identification window."""
        self._timers.pop("identification", None)
        self._decide_identification()

    def _read_reported_card(self, session_start: datetime) -> str | None:
        """Return the card value the wallbox reports, if it is valid and recent."""
        assert self.wallbox is not None
        entity_id = resolver.resolve_entity_id(self._hass, self.wallbox.identification)
        state = self._hass.states.get(entity_id) if entity_id else None
        raw = resolver.usable_state(state)
        if raw is None or state is None:
            return None
        normalized = normalize_card_uid(raw)
        if not normalized or normalized in INVALID_CARD_UIDS:
            return None
        if state.last_changed < session_start - timedelta(minutes=IDENTIFICATION_MAX_AGE_MIN):
            return None
        return normalized

    def _vehicle_location(self, context: VehicleContext) -> str | None:
        """Return the state of a vehicle's location tracker, None when unusable."""
        entity_id = resolver.resolve_entity_id(self._hass, context.vehicle.location)
        return resolver.usable_state(self._hass.states.get(entity_id) if entity_id else None)

    def _decide_identification(self) -> None:
        """Run the identification cascade for the running session."""
        assert self.wallbox is not None
        session = self._session
        if session is None or session.identification_decided:
            return
        vehicles = [context.vehicle for context in self._vehicles.values()]
        home_ids = {
            context.vehicle.id
            for context in self._vehicles.values()
            if context.vehicle.active
            and context.vehicle.identify_by_vehicle_api
            and self._vehicle_location(context) == TRACKER_STATE_HOME
        }
        result = identify(self._read_reported_card(session.start), vehicles, home_ids)
        session.identification_decided = True
        session.identification_source = result.source
        session.card_uid = result.card_uid
        session.card_label = result.card_label
        session.unknown_card = result.unknown_card
        if result.vehicle_id is not None:
            self._assign_vehicle(session, self._vehicles[result.vehicle_id], capture_start=True)
        if result.conflict:
            session.identification_conflict = True
            session.flagged = True
        self._update_unknown_card_issue(result.unknown_card)
        self._evaluate_location_conflict()
        self._resolve_late()
        self._persist()
        self._publish()

    def _update_unknown_card_issue(self, unknown: bool) -> None:
        """Raise or clear the repair issue for a card no vehicle holds."""
        subentry = self._wallbox_subentry
        assert subentry is not None
        if unknown:
            problems.async_create_unknown_card_issue(
                self._hass, wallbox_id=subentry.subentry_id, wallbox_title=subentry.title
            )
        else:
            problems.async_clear_unknown_card_issue(self._hass, wallbox_id=subentry.subentry_id)

    def _assign_vehicle(
        self, session: RunningSession, context: VehicleContext, *, capture_start: bool
    ) -> None:
        """Attach a vehicle to the session, taking its state of charge and odometer if asked."""
        session.vehicle_id = context.vehicle.id
        if capture_start:
            session.soc_start = self._read_vehicle_number(context, ROLE_SOC, None)
            session.odometer_km = self._read_vehicle_number(
                context, ROLE_ODOMETER, DISTANCE_UNIT_FACTORS_TO_KM
            )

    def _read_vehicle_number(
        self, context: VehicleContext, role_name: str, factors: dict[str, float] | None
    ) -> float | None:
        """Read a numeric vehicle role."""
        role = getattr(context.vehicle, role_name, None)
        entity_id = resolver.resolve_entity_id(self._hass, role)
        if entity_id is None:
            return None
        return resolver.read_number(self._hass.states.get(entity_id), role, factors)

    def _resolve_late(self) -> None:
        """Assign a still unassigned session once exactly one vehicle reports charging.

        Only the vehicle and its capacity are set; the state of charge and
        odometer at the start stay open.
        """
        session = self._session
        if (
            session is None
            or not session.identification_decided
            or session.vehicle_id is not None
            or session.unknown_card
            or session.state
            not in (SESSION_STATE_CHARGING, SESSION_STATE_PAUSED, SESSION_STATE_ERROR)
        ):
            return
        candidates = [
            context
            for context in self._vehicles.values()
            if context.vehicle.active
            and context.vehicle.identify_by_vehicle_api
            and self._vehicle_charge_class.get(context.vehicle.id) == CHARGE_STATE_CHARGING
        ]
        if len(candidates) != 1:
            return
        session.identification_source = IDENTIFICATION_SOURCE_VEHICLE_API
        self._assign_vehicle(session, candidates[0], capture_start=False)
        self._evaluate_location_conflict()
        self._persist()
        self._publish()

    def _evaluate_location_conflict(self) -> None:
        """Mark a session whose assigned vehicle reports being away while the wallbox charges."""
        session = self._session
        if session is None or session.vehicle_id is None:
            return
        context = self._vehicles.get(session.vehicle_id)
        if context is not None and self._vehicle_location(context) == TRACKER_STATE_NOT_HOME:
            session.location_conflict = True

    # ------------------------------------------------------------ finishing

    async def _async_finalize(self, *, stale: bool) -> None:
        """Turn the running session into a stored session."""
        session = self._session
        if session is None or self._finalizing:
            return
        self._finalizing = True
        try:
            stored = self._build_session(session, stale=stale)
            year = dt_util.as_local(session.start).year

            def _add(sessions: list[Session]) -> list[Session]:
                taken = {existing.id for existing in sessions}
                unique = stored
                counter = 2
                while unique.id in taken:
                    unique = replace(stored, id=f"{stored.id}_{counter}")
                    counter += 1
                return [*sessions, unique]

            await SessionYearStore(self._hass, year).async_update(_add)
        except Exception:
            _LOGGER.exception("The finished session could not be stored; it is kept and retried")
            self._set_timer("final", 60, self._async_on_final_timer)
            return
        finally:
            self._finalizing = False
        self._clear_session_timers()
        self._session = None
        self._open_followups = await self._async_count_followups()
        await self._async_persist()
        self._publish()
        self._evaluate_power(self._now())

    def _build_session(self, session: RunningSession, *, stale: bool) -> Session:
        """Assemble the stored session from the running one,."""
        assert self.wallbox is not None
        settings = self._settings
        context = self._vehicles.get(session.vehicle_id) if session.vehicle_id else None
        plug_end = session.plug_end or self._now()
        self._close_phase(session, plug_end)
        phases = merge_shortest_pauses(tuple(session.phases), MAX_PHASES)
        flagged = session.flagged or len(phases) < len(session.phases)

        soc_end = (
            None if stale or context is None else self._read_vehicle_number(context, ROLE_SOC, None)
        )
        plug_duration = max((plug_end - session.start).total_seconds() / 60, 0.0)
        charge_duration = sum(phase.duration_min or 0.0 for phase in phases)
        pause_duration = max(plug_duration - charge_duration, 0.0)

        authoritative = session.counters.get(session.authoritative)
        energy_measured = (
            authoritative.accumulated
            if authoritative is not None and authoritative.start_value is not None
            else None
        )
        energy_session_counter = (
            session.counters[COUNTER_SESSION].accumulated
            if len(session.counters) == 2 and COUNTER_SESSION in session.counters
            else None
        )
        if len(session.counters) == 2 and energy_measured is not None:
            other = session.counters[
                COUNTER_SESSION if session.authoritative == COUNTER_TOTAL else COUNTER_TOTAL
            ]
            largest = max(energy_measured, other.accumulated)
            if largest > 0 and abs(energy_measured - other.accumulated) > (
                COUNTER_DEVIATION_TOLERANCE * largest
            ):
                flagged = True
        if authoritative is not None and authoritative.value is not None:
            if (
                authoritative.start_value is not None
                and abs(
                    (authoritative.value - authoritative.start_value) - authoritative.accumulated
                )
                > 0.005
            ):
                _LOGGER.info("The accumulated energy differs from the counter difference")
        if energy_measured is not None and energy_measured > (
            self.wallbox.max_power_kw * POWER_TOLERANCE_FACTOR * plug_duration / 60
        ):
            flagged = True

        capacity = context.vehicle.capacity_kwh if context else None
        raw_energy = energy_raw_kwh(session.soc_start, soc_end, capacity)
        energy_kwh = derive_energy_kwh(None, energy_measured, None, None)
        estimate_uncertain = (
            session.soc_start is not None
            and soc_end is not None
            and abs(soc_end - session.soc_start) < settings.estimate_uncertain_threshold_pct
        )

        open_fields: list[str] = []
        if session.vehicle_id is None:
            open_fields.append("vehicle_id")
        if session.soc_start is None:
            open_fields.append("soc_start")
        if soc_end is None:
            open_fields.append("soc_end")
        if session.odometer_km is None:
            open_fields.append("odometer_km")
        if energy_kwh is None:
            open_fields.append("energy_kwh")
        if session.cost_incomplete:
            open_fields.append("cost")

        grid_split = self._grid_configured()
        if flagged or session.identification_conflict:
            status = SESSION_STATUS_FLAGGED
        elif open_fields:
            status = SESSION_STATUS_FOLLOWUP_OPEN
        else:
            status = SESSION_STATUS_COMPLETE

        now_iso = _iso(self._now())
        start_local = dt_util.as_local(session.start)
        suffix = session.vehicle_id or IDENTIFICATION_SOURCE_UNRESOLVED
        return Session(
            id=f"{start_local.strftime('%Y-%m-%dT%H:%M:%S')}_{suffix}",
            location=LOCATION_HOME,
            plug_start=_iso(session.start),
            identification_source=session.identification_source,
            vehicle_id=session.vehicle_id,
            vehicle_name=context.vehicle.name if context else None,
            capacity_kwh=capacity,
            wallbox_id=self.wallbox.id,
            card_uid=session.card_uid,
            card_label=session.card_label,
            identification_conflict=session.identification_conflict,
            plug_end=_iso(plug_end),
            plug_duration_min=round(plug_duration, 1),
            charge_duration_min=round(charge_duration, 1),
            pause_duration_min=round(pause_duration, 1),
            phase_count=len(phases),
            phases_recorded=True,
            soc_start=session.soc_start,
            soc_end=soc_end,
            odometer_km=session.odometer_km,
            energy_measured_kwh=_round(energy_measured, 3),
            energy_measured_session_kwh=_round(energy_session_counter, 3),
            energy_raw_kwh=_round(raw_energy, 3),
            energy_kwh=_round(energy_kwh, 3),
            energy_grid_kwh=_round(session.grid_kwh, 3) if grid_split else None,
            energy_solar_kwh=_round(session.solar_kwh, 3) if grid_split else None,
            energy_unallocated_kwh=round(session.unallocated_kwh, 3),
            estimate_uncertain=estimate_uncertain,
            cost=_round(session.cost, 4) if session.cost_started else None,
            charge_type=self.wallbox.current_type,
            charge_type_source=CHARGE_TYPE_SOURCE_WALLBOX_CONFIG,
            power_avg_kw=(
                round(energy_kwh / (charge_duration / 60), 2)
                if energy_kwh is not None and charge_duration > 0
                else None
            ),
            location_conflict=session.location_conflict,
            charge_error=session.charge_error,
            status=status,
            open_fields=tuple(open_fields),
            created_at=now_iso,
            modified_at=now_iso,
            phases=tuple(_round_phase(phase) for phase in phases),
        )

    async def _async_count_followups(self) -> int:
        """Count the stored sessions that still wait for values."""
        count = 0
        for year in await async_list_session_years(self._hass):
            count += sum(
                1
                for stored in await SessionYearStore(self._hass, year).async_load()
                if stored.status == SESSION_STATUS_FOLLOWUP_OPEN or stored.open_fields
            )
        return count

    async def async_refresh_followups(self) -> None:
        """Recount the open follow-ups after sessions were changed elsewhere."""
        self._open_followups = await self._async_count_followups()
        self._publish()

    # ------------------------------------------------------------ persistence

    def _payload(self) -> dict[str, Any]:
        """Return what is written to the runtime store."""
        payload: dict[str, Any] = {"session": self._session.to_dict() if self._session else None}
        if self._counter_detection is not None:
            payload["counter_detection"] = self._counter_detection
        return payload

    def _persist(self) -> None:
        """Write the runtime state without waiting for it."""
        self._hass.async_create_task(RuntimeStore(self._hass).async_save(self._payload()))

    async def _async_persist(self) -> None:
        """Write the runtime state and wait for it."""
        await RuntimeStore(self._hass).async_save(self._payload())

    @callback
    def _on_persist_tick(self, _now: datetime) -> None:
        """Persist the accumulators of a running session at the fixed interval."""
        if self._session is not None:
            self._persist()

    def _restore_session_timers(self) -> None:
        """Re-arm the timers of a session restored from the store."""
        session = self._session
        if session is None:
            return
        session.gap_pending = True
        for counter in session.counters.values():
            counter.timestamp = counter.timestamp or self._now()
        now = self._now()
        if session.state == SESSION_STATE_CANDIDATE:
            assert self.wallbox is not None
            remaining = self.wallbox.start_debounce_s - (now - session.start).total_seconds()
            self._set_timer("debounce", remaining, self._on_debounce_timer)
        elif session.state == SESSION_STATE_PAUSED and session.pause_since:
            remaining = MIN_PAUSE_MIN * 60 - (now - session.pause_since).total_seconds()
            self._set_timer("pause", remaining, self._on_pause_timer)
        elif session.state == SESSION_STATE_AWAITING_FINAL:
            self._set_timer("final", FINAL_VALUES_GRACE_S, self._async_on_final_timer)
        if session.state in _RUNNING_STATES and session.plug_unavailable_since:
            elapsed = (now - session.plug_unavailable_since).total_seconds()
            self._set_timer("stale", SESSION_TIMEOUT_H * 3600 - elapsed, self._on_stale_timer)
        if not session.identification_decided:
            self._schedule_identification()
        self._start_counter_check()

    # ------------------------------------------------------------- publishing

    @callback
    def async_add_listener(self, listener: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Register a callback for a new published snapshot."""
        self._listeners.append(listener)

        @callback
        def _remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _remove

    @callback
    def async_add_live_listener(self, listener: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Register a callback for a change of the live values."""
        self._live_listeners.append(listener)

        @callback
        def _remove() -> None:
            if listener in self._live_listeners:
                self._live_listeners.remove(listener)

        return _remove

    @callback
    def _on_publish_tick(self, _now: datetime) -> None:
        """Publish at the configured interval."""
        self._publish()

    def _publish(self) -> None:
        """Rebuild and publish the snapshot, and refresh the live subscribers."""
        self.snapshot = self._build_snapshot()
        for listener in list(self._listeners):
            listener()
        self._touch_live()

    def _touch_live(self) -> None:
        """Schedule a push to the live subscribers, at most once per interval."""
        if not self._live_listeners or "live" in self._timers:
            return
        self._timers["live"] = async_call_later(
            self._hass, LIVE_PUSH_INTERVAL_S, self._on_live_timer
        )

    @callback
    def _on_live_timer(self, _now: datetime) -> None:
        """Push the current live values to the subscribers."""
        self._timers.pop("live", None)
        for listener in list(self._live_listeners):
            listener()

    def _net_duration_min(self, session: RunningSession, now: datetime) -> float:
        """Return the charging time so far, the sum of the phases."""
        total = 0.0
        for phase in session.phases:
            if phase.end is not None:
                total += phase.duration_min or 0.0
                continue
            start = _parse(phase.start)
            if start is None:
                continue
            end = now
            if (
                session.state == SESSION_STATE_PAUSED
                and session.pause_since is not None
                and (now - session.pause_since).total_seconds() >= MIN_PAUSE_MIN * 60
            ):
                end = session.pause_since
            total += max((end - start).total_seconds() / 60, 0.0)
        return total

    def _vehicle_context(self) -> VehicleContext | None:
        """Return the vehicle of the running session."""
        session = self._session
        return self._vehicles.get(session.vehicle_id) if session and session.vehicle_id else None

    def _build_snapshot(self) -> WallboxSnapshot:
        """Collect everything the entities publish, resolved from the source entities."""
        session = self._session
        now = self._now()
        context = self._vehicle_context()
        active_vehicle = ACTIVE_VEHICLE_NONE
        if session is not None:
            if context is None:
                active_vehicle = ACTIVE_VEHICLE_UNRESOLVED
            elif context.vehicle.is_guest:
                active_vehicle = ACTIVE_VEHICLE_GUEST
            else:
                active_vehicle = context.vehicle.name

        share = self._last_share if self._grid_configured() else 1.0
        price = (
            allocation.effective_price(share, self._grid_price(), self._solar_price())
            if share is not None
            else None
        )
        grid_split = self._grid_configured()
        charge_end: datetime | None = None
        charge_state: str | None = None
        soc = soc_target = None
        if context is not None:
            soc = self._read_vehicle_number(context, ROLE_SOC, None)
            soc_target = self._read_vehicle_number(context, ROLE_SOC_TARGET, None)
            charge_state = self._vehicle_charge_class.get(context.vehicle.id)
            entity_id = resolver.resolve_entity_id(self._hass, context.vehicle.charge_end)
            raw_end = resolver.usable_state(self._hass.states.get(entity_id)) if entity_id else None
            charge_end = dt_util.parse_datetime(raw_end) if raw_end else None
            if charge_end is not None:
                charge_end = dt_util.as_utc(charge_end)

        return WallboxSnapshot(
            state=session.state if session else SESSION_STATE_IDLE,
            session_active=session is not None,
            active_vehicle=active_vehicle,
            session_start=session.start if session else None,
            cost=(round(session.cost, 4) if session is not None and session.cost_started else None),
            energy_grid_kwh=(
                round(session.grid_kwh, 3) if session is not None and grid_split else None
            ),
            energy_solar_kwh=(
                round(session.solar_kwh, 3) if session is not None and grid_split else None
            ),
            effective_price=round(price, 4) if price is not None else None,
            grid_share_pct=(
                round(session.last_share * 100, 1)
                if session is not None and grid_split and session.last_share is not None
                else None
            ),
            soc_start=session.soc_start if session else None,
            odometer_start=session.odometer_km if session else None,
            duration_net_min=(round(self._net_duration_min(session, now), 1) if session else None),
            vehicle_soc=soc,
            vehicle_soc_target=soc_target,
            vehicle_charge_state=charge_state,
            vehicle_charge_end=charge_end,
            open_followups=self._open_followups,
        )

    def live_payload(self) -> dict[str, Any]:
        """Return the live values for the dashboard card.

        Card identifiers, VIN, address and coordinates are never included.
        """
        assert self.wallbox is not None
        session = self._session
        now = self._now()
        context = self._vehicle_context()
        snapshot = self._build_snapshot()
        energy = None
        if session is not None:
            counter = session.counters.get(session.authoritative)
            if counter is not None and counter.start_value is not None:
                energy = round(counter.accumulated, 3)
        return {
            "state": snapshot.state,
            "active": session is not None,
            "wallbox": {"name": self.wallbox.name, "max_power_kw": self.wallbox.max_power_kw},
            "currency": self._hass.config.currency,
            "session_start": _iso(session.start) if session else None,
            "vehicle": (
                {"id": context.vehicle.id, "name": context.vehicle.name}
                if context is not None
                else None
            ),
            "vehicle_guest": bool(context and context.vehicle.is_guest),
            "identification_source": session.identification_source if session else None,
            "identification_decided": bool(session and session.identification_decided),
            "location": LOCATION_HOME if session else None,
            "soc_start": snapshot.soc_start,
            "soc": snapshot.vehicle_soc,
            "soc_target": snapshot.vehicle_soc_target,
            "charge_end": snapshot.vehicle_charge_end.isoformat()
            if snapshot.vehicle_charge_end
            else None,
            "charge_power_kw": self._power_kw,
            "energy_kwh": energy,
            "energy_grid_kwh": snapshot.energy_grid_kwh,
            "energy_solar_kwh": snapshot.energy_solar_kwh,
            "grid_share_pct": snapshot.grid_share_pct,
            "cost": snapshot.cost,
            "effective_price": snapshot.effective_price,
            "net_duration_min": snapshot.duration_net_min,
            "plug_duration_min": (
                round((now - session.start).total_seconds() / 60, 1) if session else None
            ),
            "flagged": bool(session and (session.flagged or session.identification_conflict)),
            "charge_error": bool(session and session.charge_error),
            "location_conflict": bool(session and session.location_conflict),
        }


def _round(value: float | None, digits: int) -> float | None:
    """Round an optional value."""
    return round(value, digits) if value is not None else None


def _round_phase(phase: Phase) -> Phase:
    """Round the measured values of a phase for storage."""
    return replace(
        phase,
        duration_min=_round(phase.duration_min, 1),
        energy_kwh=_round(phase.energy_kwh, 3),
        energy_grid_kwh=_round(phase.energy_grid_kwh, 3),
        energy_solar_kwh=_round(phase.energy_solar_kwh, 3),
        cost=_round(phase.cost, 4),
        power_avg_kw=_round(phase.power_avg_kw, 2),
        power_max_kw=_round(phase.power_max_kw, 2),
    )
