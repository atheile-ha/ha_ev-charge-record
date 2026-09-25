"""Session capture at the wallbox: state machine, phases, counters, identification."""

from __future__ import annotations

import logging
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from homeassistant.components.recorder import history
from homeassistant.config_entries import ConfigEntry, ConfigEntryState, ConfigSubentry
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

from . import allocation, geocoding, problems, resolver
from .const import (
    ACTIVE_VEHICLE_GUEST,
    ACTIVE_VEHICLE_NONE,
    ACTIVE_VEHICLE_UNRESOLVED,
    CANDIDATE_TRIGGER_PLUG,
    CANDIDATE_TRIGGER_POWER,
    CHARGE_END_MISSING_NO_POWER,
    CHARGE_STATE_CHARGING,
    CHARGE_STATE_CONNECTED_IDLE,
    CHARGE_STATE_DEFAULT,
    CHARGE_STATE_DISCONNECTED,
    CHARGE_STATE_ERROR,
    CHARGE_TYPE_SOURCE_ENTITY,
    CHARGE_TYPE_SOURCE_HEURISTIC,
    CHARGE_TYPE_SOURCE_WALLBOX_CONFIG,
    CHARGE_TYPE_UNKNOWN,
    COUNTER_CHECK_INTERVAL_S,
    COUNTER_DEVIATION_TOLERANCE,
    COUNTER_SESSION,
    COUNTER_TOTAL,
    CURRENT_TYPE_AC,
    CURRENT_TYPE_DC,
    CURRENT_TYPES,
    DC_POWER_THRESHOLD_KW,
    DEFAULT_ESTIMATE_UNCERTAIN_THRESHOLD_PCT,
    DISTANCE_UNIT_FACTORS_TO_KM,
    DOMAIN,
    ENERGY_UNIT_FACTORS_TO_KWH,
    ERROR_CLASS_ERROR,
    ERROR_CLASS_OK,
    ERROR_DEBOUNCE_S,
    FINAL_VALUES_GRACE_S,
    GRID_POWER_WINDOW_S,
    HOME_VEHICLE_START_DELAY_S,
    IDENTIFICATION_SOURCE_MANUAL,
    IDENTIFICATION_SOURCE_UNRESOLVED,
    IDENTIFICATION_SOURCE_VEHICLE_API,
    LIVE_BLOCK_EXTERNAL,
    LIVE_BLOCK_WALLBOX,
    LIVE_PUSH_INTERVAL_S,
    LOCATION_EXTERNAL,
    LOCATION_HOME,
    LOCATION_HOME_NO_WALLBOX,
    MAX_PHASES,
    MIN_PAUSE_MIN,
    MIN_PLAUSIBILITY_INTERVAL_S,
    PERSIST_INTERVAL_S,
    PLUG_REPORT_UNAVAILABLE,
    PLUG_STATE_CONNECTED,
    PLUG_STATE_NOT_CONNECTED,
    POWER_TOLERANCE_FACTOR,
    POWER_UNIT_FACTORS_TO_KW,
    ROLE_CHARGE_POWER,
    ROLE_CHARGE_STATE,
    ROLE_CHARGE_TYPE,
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
    ROLE_RANGE,
    ROLE_SOC,
    ROLE_SOC_TARGET,
    SAME_VEHICLE_POWER_TOLERANCE_MIN_KW,
    SAME_VEHICLE_POWER_TOLERANCE_RATIO,
    SAME_VEHICLE_WINDOW_S,
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
    Card,
    EntityRole,
    HubSettings,
    MergeCheck,
    MergeRejectedError,
    Phase,
    Session,
    Vehicle,
    Wallbox,
    derive_energy_kwh,
    merge_sessions,
    merge_shortest_pauses,
)
from .store import (
    MissingSessionsError,
    RuntimeStore,
    SessionYearStore,
    async_list_session_years,
    replace_by_merged,
)

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


def _matching_cards(reported_card: str, vehicles: Sequence[Vehicle]) -> list[tuple[Vehicle, Card]]:
    """Return the active cards of active vehicles that begin or end with the reported value.

    A wallbox may report only the start or only the end of the serial number, so
    both count. A card that matches at both ends is still one match.
    """
    return [
        (vehicle, card)
        for vehicle in vehicles
        if vehicle.active
        for card in vehicle.cards
        if card.active and (card.uid.startswith(reported_card) or card.uid.endswith(reported_card))
    ]


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

    A reported value matches a stored card when it forms the start or the end
    of the full identifier. A value that matches several cards is no match. A
    valid value that matches no card at all stops the cascade: the card is
    someone else's.
    """
    card_uid: str | None = None
    if reported_card is not None:
        matches = _matching_cards(reported_card, vehicles)
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


@dataclass(frozen=True, slots=True)
class LateIdentification:
    """The outcome of matching a card that was read after the cascade had decided.

    vehicle_id and source are those the session has afterwards: the ones it
    had if the card changes nothing.
    """

    vehicle_id: str | None
    source: str
    card_uid: str
    card_label: str | None = None
    conflict: bool = False
    unknown_card: bool = False


def identify_late(
    reported_card: str,
    vehicles: Sequence[Vehicle],
    *,
    vehicle_id: str | None,
    source: str,
) -> LateIdentification:
    """Apply a card read after the cascade had decided to the session it belongs to.

    vehicle_id and source are what the session has by then. A card that
    matches exactly one stored card assigns an unassigned session to that
    card's vehicle, and takes over a session the vehicle report assigned to
    another vehicle, which is a conflict. A card that matches no stored card
    leaves an unassigned session unassigned and is a conflict for an assigned
    one. A value that matches several cards is no match and changes nothing.
    """
    matches = _matching_cards(reported_card, vehicles)
    if len(matches) == 1:
        vehicle, card = matches[0]
        return LateIdentification(
            vehicle_id=vehicle.id,
            source=card.type,
            card_uid=card.uid,
            card_label=card.label,
            conflict=vehicle_id is not None and vehicle_id != vehicle.id,
        )
    if not matches:
        return LateIdentification(
            vehicle_id=vehicle_id,
            source=source,
            card_uid=reported_card,
            conflict=vehicle_id is not None,
            unknown_card=True,
        )
    return LateIdentification(vehicle_id=vehicle_id, source=source, card_uid=reported_card)


def should_discard(
    *,
    ended_by_unplug: bool,
    counter_readable: bool,
    counter_increased: bool,
    phase_begun: bool,
    charge_error: bool,
    flagged: bool,
    identification_conflict: bool,
) -> bool:
    """Return whether a finished session holds nothing and is not stored.

    Only certainty discards. The session must have ended by the vehicle being
    unplugged, the counter that carries the energy must have been readable
    and not have risen, and there must have been no phase, no reported
    charging error and no marking. Anything else keeps the session.
    """
    return (
        ended_by_unplug
        and counter_readable
        and not (
            counter_increased or phase_begun or charge_error or flagged or identification_conflict
        )
    )


def is_wallbox_vehicle(
    *,
    session_age_s: float,
    charge_edge_age_s: float | None,
    wallbox_charging: bool,
    wallbox_power_kw: float | None,
    vehicle_power_kw: float | None,
) -> bool:
    """Return whether a vehicle that reports charging is the car at the wallbox.

    Called for a vehicle at home while the wallbox session has no vehicle. The
    wallbox session must have begun, or its charging power must have risen or
    fallen, within the window, or the wallbox must be charging now. When both
    powers are known and positive and differ by more than the larger of the
    absolute and the relative tolerance, it is another car.
    """
    near = (
        wallbox_charging
        or session_age_s <= SAME_VEHICLE_WINDOW_S
        or (charge_edge_age_s is not None and charge_edge_age_s <= SAME_VEHICLE_WINDOW_S)
    )
    if not near:
        return False
    if wallbox_power_kw and wallbox_power_kw > 0 and vehicle_power_kw and vehicle_power_kw > 0:
        tolerance = max(
            SAME_VEHICLE_POWER_TOLERANCE_MIN_KW,
            SAME_VEHICLE_POWER_TOLERANCE_RATIO * wallbox_power_kw,
        )
        if abs(wallbox_power_kw - vehicle_power_kw) > tolerance:
            return False
    return True


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
    # The counter could not be read when the session began; its start value is
    # the first reading after that.
    started_late: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the runtime store."""
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "start_value": self.start_value,
            "accumulated": self.accumulated,
            "started_late": self.started_late,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> _Counter:
        """Deserialize from the runtime store."""
        return cls(
            value=data.get("value"),
            timestamp=_parse(data.get("timestamp")),
            start_value=data.get("start_value"),
            accumulated=data.get("accumulated", 0.0),
            started_late=data.get("started_late", False),
        )


@dataclass
class RunningSession:
    """The session in progress. Serialized to the runtime store at every transition."""

    start: datetime
    state: str = SESSION_STATE_CANDIDATE
    state_since: datetime | None = None
    trigger: str = CANDIDATE_TRIGGER_PLUG
    power_since: datetime | None = None
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
    same_vehicles: list[str] = field(default_factory=list)

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
            "state_since": self.state_since.isoformat() if self.state_since else None,
            "trigger": self.trigger,
            "power_since": self.power_since.isoformat() if self.power_since else None,
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
            "same_vehicles": list(self.same_vehicles),
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
            state_since=_parse(data.get("state_since")) or start,
            trigger=data.get("trigger", CANDIDATE_TRIGGER_POWER),
            power_since=_parse(data.get("power_since")),
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
            same_vehicles=list(data.get("same_vehicles", [])),
        )


@dataclass
class RunningVehicleSession:
    """A charging session detected from a vehicle's own charge_state alone (4.7, 7.4, 7.5).

    Independent of the wallbox: begins the moment the vehicle first reports
    charging and ends when it reports disconnected. location is decided once,
    when the session begins, and never changes afterwards. Serialized to the
    runtime store at every transition, alongside the wallbox session.
    """

    vehicle_id: str
    start: datetime
    location: str
    state: str = SESSION_STATE_CHARGING
    state_since: datetime | None = None
    last_valid: datetime | None = None
    unavailable_since: datetime | None = None
    plug_end: datetime | None = None
    phases: list[Phase] = field(default_factory=list)
    pause_since: datetime | None = None
    soc_start: float | None = None
    odometer_km: float | None = None
    energy_session_kwh: float | None = None
    charge_type: str = CHARGE_TYPE_UNKNOWN
    charge_type_source: str | None = None
    charge_error: bool = False
    flagged: bool = False
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_reported_at: datetime | None = None
    address_retry_pending: bool = False

    def open_phase(self) -> Phase | None:
        """Return the phase that is still open, if any."""
        if self.phases and self.phases[-1].end is None:
            return self.phases[-1]
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the runtime store."""
        return {
            "vehicle_id": self.vehicle_id,
            "start": self.start.isoformat(),
            "location": self.location,
            "state": self.state,
            "state_since": self.state_since.isoformat() if self.state_since else None,
            "last_valid": self.last_valid.isoformat() if self.last_valid else None,
            "unavailable_since": (
                self.unavailable_since.isoformat() if self.unavailable_since else None
            ),
            "plug_end": self.plug_end.isoformat() if self.plug_end else None,
            "phases": [phase.to_dict() for phase in self.phases],
            "pause_since": self.pause_since.isoformat() if self.pause_since else None,
            "soc_start": self.soc_start,
            "odometer_km": self.odometer_km,
            "energy_session_kwh": self.energy_session_kwh,
            "charge_type": self.charge_type,
            "charge_type_source": self.charge_type_source,
            "charge_error": self.charge_error,
            "flagged": self.flagged,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_reported_at": (
                self.location_reported_at.isoformat() if self.location_reported_at else None
            ),
            "address_retry_pending": self.address_retry_pending,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunningVehicleSession:
        """Deserialize from the runtime store."""
        start = _parse(data["start"])
        if start is None:
            raise ValueError("stored vehicle session has an unreadable start")
        return cls(
            vehicle_id=data["vehicle_id"],
            start=start,
            location=data["location"],
            state=data.get("state", SESSION_STATE_CHARGING),
            state_since=_parse(data.get("state_since")) or start,
            last_valid=_parse(data.get("last_valid")),
            unavailable_since=_parse(data.get("unavailable_since")),
            plug_end=_parse(data.get("plug_end")),
            phases=[Phase.from_dict(phase) for phase in data.get("phases", [])],
            pause_since=_parse(data.get("pause_since")),
            soc_start=data.get("soc_start"),
            odometer_km=data.get("odometer_km"),
            energy_session_kwh=data.get("energy_session_kwh"),
            charge_type=data.get("charge_type", CHARGE_TYPE_UNKNOWN),
            charge_type_source=data.get("charge_type_source"),
            charge_error=data.get("charge_error", False),
            flagged=data.get("flagged", False),
            address=data.get("address"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            location_reported_at=_parse(data.get("location_reported_at")),
            address_retry_pending=data.get("address_retry_pending", False),
        )


@dataclass(frozen=True, slots=True)
class VehicleContext:
    """A vehicle together with what is needed to read and classify its entities."""

    vehicle: Vehicle
    subentry_id: str
    title: str
    mapping: DeviceMapping | None


@dataclass(frozen=True, slots=True)
class _PendingVehicleStart:
    """A charging report at home whose session start waits for the wallbox."""

    reported_at: datetime
    soc: float | None
    odometer_km: float | None


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


@dataclass(frozen=True, slots=True)
class VehicleSnapshot:
    """What a vehicle's own entities publish (11.4, 11.5), independent of the wallbox."""

    session_active: bool
    session_state: str | None
    session_location: str | None
    session_soc_start: float | None
    session_odometer_start: float | None
    session_energy_kwh: float | None
    session_duration_net_min: float | None
    charge_end: datetime | None


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
        self._vehicle_sessions: dict[str, RunningVehicleSession] = {}
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
        self._vehicle_plug_class: dict[str, str | None] = {}
        self._vehicle_rearm: set[str] = set()
        self._vehicle_pending: dict[str, _PendingVehicleStart] = {}
        self._units_seen: dict[str, str | None] = {}
        self._counter_detection: dict[str, str] | None = None
        self._open_followups = 0
        self._finalizing = False
        self._card_reader: resolver.IdentificationReader | None = None
        self._direct_read_failure: str | None = None
        self.snapshot = self._build_snapshot()
        self.vehicle_snapshots: dict[str, VehicleSnapshot] = {}

    # ------------------------------------------------------------------ setup

    @property
    def settings(self) -> HubSettings:
        """Return the global settings."""
        return self._settings

    @property
    def wallbox_subentry_id(self) -> str | None:
        """Return the id of the wallbox subentry."""
        return self._wallbox_subentry.subentry_id if self._wallbox_subentry else None

    @property
    def vehicle_contexts(self) -> list[VehicleContext]:
        """Return every configured vehicle, active or not."""
        return list(self._vehicles.values())

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
        self._card_reader = resolver.IdentificationReader(
            self._hass, self.wallbox, self._wallbox_mapping
        )
        await self._card_reader.async_prepare()
        problems.async_clear_direct_read_issues(self._hass, wallbox_id=wallbox_subentry.subentry_id)
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
        self._vehicle_rearm = set(stored.get("vehicle_rearm", []))
        if stored.get("session"):
            try:
                self._session = RunningSession.from_dict(stored["session"])
            except KeyError, ValueError:
                _LOGGER.exception("The stored session could not be restored and is dropped")
        for vehicle_id, data in stored.get("vehicle_sessions", {}).items():
            try:
                self._vehicle_sessions[vehicle_id] = RunningVehicleSession.from_dict(data)
            except KeyError, ValueError:
                _LOGGER.exception(
                    "The stored external session of a vehicle could not be restored and is dropped"
                )
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
        self._restore_vehicle_session_timers()
        self._apply_current_states()
        self._publish()
        self._hass.async_create_task(self._async_retry_pending_addresses(), eager_start=False)
        return True

    async def async_unload(self) -> None:
        """Stop observing and cancel every timer. The running session stays in the store."""
        for unsub in [*self._unsubs, *self._source_unsubs]:
            unsub()
        self._unsubs.clear()
        self._source_unsubs.clear()
        for name in list(self._timers):
            self._cancel_timer(name)
        if self._card_reader is not None:
            self._card_reader.cancel()
        self._listeners.clear()
        self._live_listeners.clear()
        if self._session is not None or self._vehicle_sessions:
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
            self._watch_role(
                vehicle.plug_state, lambda s, c=context: self._on_vehicle_plug_state(c, s)
            )
            self._watch_role(vehicle.location, lambda _s: self._on_vehicle_location())
            self._watch_role(
                vehicle.charge_type, lambda s, c=context: self._on_vehicle_charge_type_role(c, s)
            )
            self._watch_role(
                vehicle.energy_session,
                lambda s, c=context: self._on_vehicle_energy_session_role(c, s),
            )
            for role in (
                vehicle.soc,
                vehicle.soc_target,
                vehicle.odometer,
                vehicle.charge_end,
                vehicle.charge_power,
                vehicle.range,
            ):
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

    def _maybe_start_candidate(self, now: datetime) -> None:
        """Start a candidate if none exists and something calls for one.

        The connector reporting a vehicle does, whatever the power. Without a
        usable connector report, power above the threshold does too, as long
        as the connector does not say that nothing is plugged in.
        """
        if self._session is not None:
            return
        if self._plug_usable and self._plug_class == PLUG_STATE_CONNECTED:
            self._start_candidate(now, CANDIDATE_TRIGGER_PLUG)
        elif self._power_active() and self._plug_class != PLUG_STATE_NOT_CONNECTED:
            self._start_candidate(now, CANDIDATE_TRIGGER_POWER)

    def _evaluate_power(self, now: datetime) -> None:
        """Move the state machine according to the charging power."""
        session = self._session
        active = self._power_active()
        if session is None:
            self._maybe_start_candidate(now)
            return
        if session.state == SESSION_STATE_CANDIDATE:
            if active:
                session.power_since = session.power_since or now
            else:
                session.power_since = None
                if session.trigger == CANDIDATE_TRIGGER_POWER:
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
        if klass != self._plug_class:
            _LOGGER.debug("Plug state '%s' reads as %s", raw, klass)
        if klass is not None:
            self._plug_class = klass
        if klass == PLUG_STATE_NOT_CONNECTED and session is not None:
            self._unplug(now)
        self._maybe_start_candidate(now)
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
            counter.started_late = True
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
        """Classify a vehicle's charge state, drive its own session, and resolve the wallbox's."""
        now = self._now()
        raw = resolver.usable_state(state)
        if raw is None:
            self._vehicle_source_unavailable(context, now)
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
        self._vehicle_source_available(context.vehicle.id, now)
        if klass is not None:
            self._drive_vehicle_session(context, klass, now)
        self._resolve_late()
        self._touch_live()

    @callback
    def _on_vehicle_location(self) -> None:
        """Re-check the location of the assigned vehicle."""
        self._evaluate_location_conflict()
        self._touch_live()

    @callback
    def _on_vehicle_charge_type_role(self, context: VehicleContext, state: State | None) -> None:
        """Lock a vehicle's own session to the first unambiguous reported charge type (E32, I21)."""
        session = self._vehicle_sessions.get(context.vehicle.id)
        if session is None:
            return
        raw = resolver.usable_state(state)
        if raw is None:
            return
        mapping = context.mapping.role_values(ROLE_CHARGE_TYPE) if context.mapping else {}
        klass = resolver.classify_charge_type(raw, mapping)
        if session.charge_type_source == CHARGE_TYPE_SOURCE_ENTITY:
            if klass in CURRENT_TYPES and klass != session.charge_type:
                _LOGGER.warning(
                    "Vehicle %s reported charge type %s, which differs from the established %s; "
                    "the session keeps %s",
                    context.vehicle.id,
                    klass,
                    session.charge_type,
                    session.charge_type,
                )
            return
        if klass not in CURRENT_TYPES:
            return
        session.charge_type = klass
        session.charge_type_source = CHARGE_TYPE_SOURCE_ENTITY
        self._touch_live()

    @callback
    def _on_vehicle_energy_session_role(self, context: VehicleContext, state: State | None) -> None:
        """Keep the last reported session energy of a vehicle's own running session."""
        session = self._vehicle_sessions.get(context.vehicle.id)
        if session is None:
            return
        value = resolver.read_number(
            state, context.vehicle.energy_session, ENERGY_UNIT_FACTORS_TO_KWH
        )
        if value is not None:
            session.energy_session_kwh = value
            self._touch_live()

    # ----------------------------------------------------- state transitions

    def _start_candidate(self, now: datetime, trigger: str) -> None:
        """Create the candidate at the moment the plug reports a vehicle or the power rises.

        The candidate holds no phase. Its time and counter readings become
        those of the session if it is confirmed.
        """
        assert self.wallbox is not None
        session = RunningSession(
            start=now,
            state=SESSION_STATE_CANDIDATE,
            state_since=now,
            trigger=trigger,
            power_since=now if self._power_active() else None,
        )
        _LOGGER.debug("A candidate begins, started by the %s", trigger)
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
        session.plug_last_valid = now
        self._session = session
        if not self._plug_usable:
            self._plug_unavailable(session, now)
        self._start_counter_check()
        self._begin_identification(session)
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
        if self._card_reader is not None:
            self._card_reader.cancel()

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
        session = self._session
        if session.state != state or session.state_since is None:
            session.state_since = self._now()
        if session.state != state:
            _LOGGER.debug("Session state %s -> %s", session.state, state)
        session.state = state
        self._persist()
        self._publish()

    @callback
    def _on_debounce_timer(self, _now: datetime) -> None:
        """Confirm the candidate once the debounce time has passed."""
        self._timers.pop("debounce", None)
        self._confirm_candidate(self._now())

    def _confirm_candidate(self, now: datetime) -> None:
        """Turn the candidate into a running session.

        A candidate that the power created is dropped if the power did not
        hold. One that the plug created stays: it charges if the power is
        above the threshold and waits otherwise.
        """
        session = self._session
        if session is None or session.state != SESSION_STATE_CANDIDATE:
            return
        active = self._power_active()
        if session.trigger == CANDIDATE_TRIGGER_POWER and not active:
            self._discard_candidate()
            return
        if active:
            if not session.phases:
                self._open_phase(session, session.power_since or now)
            self._enter(SESSION_STATE_CHARGING)
        else:
            self._enter(SESSION_STATE_PAUSED)
        if self._error_class == ERROR_CLASS_ERROR:
            self._set_timer("error", ERROR_DEBOUNCE_S, self._on_error_timer)

    def _discard_candidate(self) -> None:
        """Drop a candidate that did not last."""
        _LOGGER.debug("The candidate is dropped")
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
        """Start a new phase, joining the shortest pauses first when the limit is reached.

        The first phase of a session also starts the second sequence of reads
        of the identification.
        """
        first = not session.phases
        if len(session.phases) >= MAX_PHASES:
            session.phases = list(merge_shortest_pauses(tuple(session.phases), MAX_PHASES - 1))
            session.flagged = True
        session.phases.append(Phase(start=_iso(now), power_max_kw=self._power_kw))
        _LOGGER.debug("Phase %d begins", len(session.phases))
        if first and self._card_reader is not None:
            self._card_reader.begin_charging()

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
        if self._card_reader is not None:
            self._card_reader.stop()
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
        if self._card_reader is not None:
            self._card_reader.stop()
        end = session.plug_last_valid or session.start
        self._close_phase(session, end)
        session.plug_end = end
        session.flagged = True
        session.state = SESSION_STATE_AWAITING_FINAL
        session.state_since = self._now()
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

    def _begin_identification(self, session: RunningSession) -> None:
        """Start reading the identification for the session, if it comes from the device."""
        assert self._card_reader is not None
        self._card_reader.begin(self._on_reader_event, since=session.start)

    @callback
    def _on_reader_event(self, event: resolver.ReadEvent) -> None:
        """Handle a step of reading the identification from the device."""
        assert self._card_reader is not None
        if event is resolver.ReadEvent.VALUE:
            self._report_read_failure(None)
            session = self._session
            if session is not None and not session.identification_decided:
                _LOGGER.debug("Identification read; it is held for the decision")
            self._assign_late_card()
        elif event is resolver.ReadEvent.EXHAUSTED:
            self._report_read_failure(self._card_reader.failure)
        self._touch_live()

    def _report_read_failure(self, failure: str | None) -> None:
        """Raise or clear the repair issue for a failed reading, and log a change once."""
        subentry = self._wallbox_subentry
        assert subentry is not None
        problems.check_direct_read(
            self._hass,
            failure=failure,
            wallbox_id=subentry.subentry_id,
            wallbox_title=subentry.title,
        )
        if failure is not None and failure != self._direct_read_failure:
            _LOGGER.warning("The identification could not be read from the wallbox: %s", failure)
        elif failure is not None:
            _LOGGER.debug("The identification could not be read from the wallbox: %s", failure)
        elif self._direct_read_failure is not None:
            _LOGGER.info("The identification can be read from the wallbox again")
        self._direct_read_failure = failure

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
        assert self._card_reader is not None
        vehicles = [context.vehicle for context in self._vehicles.values()]
        home_ids = {
            context.vehicle.id
            for context in self._vehicles.values()
            if context.vehicle.active
            and context.vehicle.identify_by_vehicle_api
            and self._vehicle_location(context) == TRACKER_STATE_HOME
        }
        result = identify(self._card_reader.value(session.start), vehicles, home_ids)
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
        _LOGGER.debug(
            "Identification decided: source %s, vehicle %s, card read %s, conflict %s",
            result.source,
            result.vehicle_id,
            result.card_uid is not None,
            result.conflict,
        )
        self._update_unknown_card_issue(result.unknown_card)
        self._evaluate_location_conflict()
        self._resolve_late()
        self._persist()
        self._publish()

    def _assign_late_card(self) -> None:
        """Apply a card that was read after the cascade had decided.

        Only the assignment changes: energy, cost and phases stay as they are.
        A vehicle that is newly assigned or replaced loses the start values
        that were taken for another vehicle, and they stay open.
        """
        assert self._card_reader is not None
        session = self._session
        if (
            session is None
            or not session.identification_decided
            or session.card_uid is not None
            or session.state == SESSION_STATE_AWAITING_FINAL
        ):
            return
        reported = self._card_reader.value(session.start)
        if reported is None:
            _LOGGER.debug("A read finished, but there is no identification to apply")
            return
        result = identify_late(
            reported,
            [context.vehicle for context in self._vehicles.values()],
            vehicle_id=session.vehicle_id,
            source=session.identification_source,
        )
        session.card_uid = result.card_uid
        session.card_label = result.card_label
        session.unknown_card = result.unknown_card
        session.identification_source = result.source
        if result.vehicle_id != session.vehicle_id and result.vehicle_id is not None:
            self._assign_vehicle(session, self._vehicles[result.vehicle_id], capture_start=False)
            session.soc_start = None
            session.odometer_km = None
            session.location_conflict = False
        if result.conflict:
            session.identification_conflict = True
            session.flagged = True
        _LOGGER.debug(
            "Identification read after the decision: source %s, vehicle %s, conflict %s, "
            "card unknown %s",
            result.source,
            result.vehicle_id,
            result.conflict,
            result.unknown_card,
        )
        self._update_unknown_card_issue(result.unknown_card)
        self._evaluate_location_conflict()
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

        The vehicle and its capacity are set immediately. The state of
        charge and odometer at the start are looked up from the recorder in
        the background (7.8) and applied if the session is still the same
        one when the lookup returns; they stay open if the recorder has no
        answer, the same as before a card or vehicle-api match ever ran.
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
        self._start_late_history(candidates[0], session.start)
        self._persist()
        self._publish()

    def _start_late_history(self, context: VehicleContext, session_start: datetime) -> None:
        """Look up the start values of a late-assigned session, without waiting for it."""
        if context.vehicle.soc is None and context.vehicle.odometer is None:
            return
        self._hass.async_create_task(
            self._async_apply_late_history(context, session_start), eager_start=False
        )

    async def _async_apply_late_history(
        self, context: VehicleContext, session_start: datetime
    ) -> None:
        """Read soc_start and odometer_km from the recorder, apply them if still open (7.8)."""
        soc_start = await async_role_history_number(
            self._hass, context.vehicle.soc, session_start, None
        )
        odometer_km = await async_role_history_number(
            self._hass, context.vehicle.odometer, session_start, DISTANCE_UNIT_FACTORS_TO_KM
        )
        if soc_start is None and odometer_km is None:
            return
        session = self._session
        if (
            session is None
            or session.start != session_start
            or session.vehicle_id != context.vehicle.id
        ):
            return
        if soc_start is not None and session.soc_start is None:
            session.soc_start = soc_start
        if odometer_km is not None and session.odometer_km is None:
            session.odometer_km = odometer_km
        self._persist()
        self._touch_live()

    def _evaluate_location_conflict(self) -> None:
        """Mark a session whose assigned vehicle reports being away while the wallbox charges."""
        session = self._session
        if session is None or session.vehicle_id is None:
            return
        context = self._vehicles.get(session.vehicle_id)
        if context is not None and self._vehicle_location(context) == TRACKER_STATE_NOT_HOME:
            session.location_conflict = True

    # ------------------------------------------------------- vehicle sessions

    def _vehicle_pause_timer_name(self, vehicle_id: str) -> str:
        """Return the timer name for a vehicle's own minimum-pause timer."""
        return f"vehicle_pause_{vehicle_id}"

    def _vehicle_stale_timer_name(self, vehicle_id: str) -> str:
        """Return the timer name for a vehicle's own source-unavailable timeout."""
        return f"vehicle_stale_{vehicle_id}"

    def _cancel_vehicle_timers(self, vehicle_id: str) -> None:
        """Cancel every timer that belongs to a vehicle's own session."""
        self._cancel_timer(self._vehicle_pause_timer_name(vehicle_id))
        self._cancel_timer(self._vehicle_stale_timer_name(vehicle_id))

    def _vehicle_source_unavailable(self, context: VehicleContext, now: datetime) -> None:
        """Note that a vehicle's charge state is unusable and start its stale timeout (7.5)."""
        session = self._vehicle_sessions.get(context.vehicle.id)
        if session is None or session.state == SESSION_STATE_AWAITING_FINAL:
            return
        if session.unavailable_since is None:
            session.unavailable_since = now
        name = self._vehicle_stale_timer_name(context.vehicle.id)
        if name not in self._timers:
            elapsed = (now - session.unavailable_since).total_seconds()
            self._set_timer(
                name,
                SESSION_TIMEOUT_H * 3600 - elapsed,
                callback(lambda _now, c=context: self._on_vehicle_stale_timer(c)),
            )

    def _vehicle_source_available(self, vehicle_id: str, now: datetime) -> None:
        """Note that a vehicle's charge state is usable again, canceling its stale timeout."""
        session = self._vehicle_sessions.get(vehicle_id)
        if session is None:
            return
        session.last_valid = now
        if session.unavailable_since is not None:
            session.unavailable_since = None
            self._cancel_timer(self._vehicle_stale_timer_name(vehicle_id))

    def _start_vehicle_session(
        self,
        context: VehicleContext,
        now: datetime,
        *,
        pending: _PendingVehicleStart | None = None,
    ) -> RunningVehicleSession:
        """Begin a vehicle's own session, deciding its location once from the tracker (7.4).

        Home-zone means home_no_wallbox; anything else, including an unusable
        tracker, means external, with coordinates captured for geocoding. A
        held-back start brings the readings taken at the report.
        """
        location = (
            LOCATION_HOME_NO_WALLBOX
            if self._vehicle_location(context) == TRACKER_STATE_HOME
            else LOCATION_EXTERNAL
        )
        session = RunningVehicleSession(
            vehicle_id=context.vehicle.id,
            start=now,
            location=location,
            state=SESSION_STATE_CHARGING,
            state_since=now,
            last_valid=now,
            soc_start=(
                pending.soc
                if pending is not None
                else self._read_vehicle_number(context, ROLE_SOC, None)
            ),
            odometer_km=(
                pending.odometer_km
                if pending is not None
                else self._read_vehicle_number(context, ROLE_ODOMETER, DISTANCE_UNIT_FACTORS_TO_KM)
            ),
        )
        if location == LOCATION_EXTERNAL:
            entity_id = resolver.resolve_entity_id(self._hass, context.vehicle.location)
            tracker = self._hass.states.get(entity_id) if entity_id else None
            if tracker is not None:
                session.latitude = tracker.attributes.get("latitude")
                session.longitude = tracker.attributes.get("longitude")
                session.location_reported_at = tracker.last_changed
            if session.latitude is not None and session.longitude is not None:
                session.address_retry_pending = True
                self._start_geocode(context.vehicle.id, session.start)
        self._vehicle_sessions[context.vehicle.id] = session
        _LOGGER.debug(
            "An external session begins for vehicle %s, location %s", context.vehicle.id, location
        )
        return session

    def _drive_vehicle_session(self, context: VehicleContext, klass: str, now: datetime) -> None:
        """Move a vehicle's own session according to its charge state class (4.7, 7.4, 7.5).

        Only the charging class begins a session; connected_idle and error
        only ever continue one that already exists, and disconnected always
        ends it, also while the wallbox session names this vehicle. A session
        does not begin for a vehicle the wallbox session names, for the car at
        the wallbox, nor for a vehicle that has reported charging since its
        wallbox session ended until it has reported anything else. A vehicle
        at home begins its session only after a waiting time, so a wallbox
        that reports the plug later than the vehicle reports charging still
        claims it.
        """
        vehicle_id = context.vehicle.id
        session = self._vehicle_sessions.get(vehicle_id)
        if session is not None and session.state == SESSION_STATE_AWAITING_FINAL:
            return
        if klass != CHARGE_STATE_CHARGING and vehicle_id in self._vehicle_rearm:
            self._vehicle_rearm.discard(vehicle_id)
            self._persist()
        if klass == CHARGE_STATE_DISCONNECTED:
            self._cancel_vehicle_pending(vehicle_id)
            if session is not None:
                self._end_vehicle_session(context, session, now)
            return
        if session is None:
            if klass != CHARGE_STATE_CHARGING or vehicle_id in self._vehicle_pending:
                return
            if self._vehicle_start_suppressed(context, now):
                return
            if self._vehicle_location(context) == TRACKER_STATE_HOME:
                self._begin_vehicle_pending(context, now)
                return
            session = self._start_vehicle_session(context, now)

        if klass == CHARGE_STATE_CHARGING:
            self._cancel_timer(self._vehicle_pause_timer_name(vehicle_id))
            if session.open_phase() is None:
                self._open_vehicle_phase(session, now)
            session.pause_since = None
            self._enter_vehicle_state(session, SESSION_STATE_CHARGING)
        elif klass == CHARGE_STATE_CONNECTED_IDLE:
            if session.state != SESSION_STATE_PAUSED:
                session.pause_since = now
                self._set_timer(
                    self._vehicle_pause_timer_name(vehicle_id),
                    MIN_PAUSE_MIN * 60,
                    callback(lambda _now, c=context: self._on_vehicle_pause_timer(c)),
                )
                self._enter_vehicle_state(session, SESSION_STATE_PAUSED)
        elif klass == CHARGE_STATE_ERROR and session.state != SESSION_STATE_ERROR:
            self._cancel_timer(self._vehicle_pause_timer_name(vehicle_id))
            end = session.pause_since if session.state == SESSION_STATE_PAUSED else now
            self._close_vehicle_phase(session, end)
            session.pause_since = None
            session.charge_error = True
            self._enter_vehicle_state(session, SESSION_STATE_ERROR)

    def _vehicle_start_suppressed(self, context: VehicleContext, reported_at: datetime) -> bool:
        """Whether a charging report, made at the given moment, must not begin a session."""
        vehicle_id = context.vehicle.id
        if self._session is not None and self._session.vehicle_id == vehicle_id:
            return True
        return vehicle_id in self._vehicle_rearm or self._wallbox_covers_vehicle(
            context, reported_at
        )

    def _vehicle_pending_timer_name(self, vehicle_id: str) -> str:
        """Return the timer name for the delayed start of a vehicle's own session at home."""
        return f"vehicle_pending_{vehicle_id}"

    def _begin_vehicle_pending(self, context: VehicleContext, now: datetime) -> None:
        """Hold back the start of a vehicle's session at home for the waiting time.

        The moment of the report and the readings of that moment are kept, so
        a session that begins after the waiting time starts at the report.
        """
        vehicle_id = context.vehicle.id
        self._vehicle_pending[vehicle_id] = _PendingVehicleStart(
            reported_at=now,
            soc=self._read_vehicle_number(context, ROLE_SOC, None),
            odometer_km=self._read_vehicle_number(
                context, ROLE_ODOMETER, DISTANCE_UNIT_FACTORS_TO_KM
            ),
        )
        self._set_timer(
            self._vehicle_pending_timer_name(vehicle_id),
            HOME_VEHICLE_START_DELAY_S,
            callback(lambda _now, c=context: self._on_vehicle_pending_timer(c)),
        )
        _LOGGER.debug(
            "Vehicle %s reports charging at home; its own session waits %d s for the wallbox",
            vehicle_id,
            HOME_VEHICLE_START_DELAY_S,
        )

    def _cancel_vehicle_pending(self, vehicle_id: str) -> None:
        """Drop a held-back start of a vehicle's session."""
        self._cancel_timer(self._vehicle_pending_timer_name(vehicle_id))
        self._vehicle_pending.pop(vehicle_id, None)

    @callback
    def _on_vehicle_pending_timer(self, context: VehicleContext) -> None:
        """Begin the held-back session unless the wallbox claimed the vehicle meanwhile."""
        vehicle_id = context.vehicle.id
        self._timers.pop(self._vehicle_pending_timer_name(vehicle_id), None)
        pending = self._vehicle_pending.pop(vehicle_id, None)
        if pending is None or vehicle_id in self._vehicle_sessions:
            return
        klass = self._vehicle_charge_class.get(vehicle_id)
        if klass in (None, CHARGE_STATE_DISCONNECTED):
            return
        now = self._now()
        if self._vehicle_start_suppressed(
            context, pending.reported_at
        ) or self._vehicle_start_suppressed(context, now):
            _LOGGER.debug("Vehicle %s is the car at the wallbox; no own session", vehicle_id)
            return
        session = self._start_vehicle_session(context, pending.reported_at, pending=pending)
        self._open_vehicle_phase(session, pending.reported_at)
        self._enter_vehicle_state(session, SESSION_STATE_CHARGING)
        if klass != CHARGE_STATE_CHARGING:
            self._drive_vehicle_session(context, klass, now)
        self._touch_live()

    def _wallbox_covers_vehicle(self, context: VehicleContext, now: datetime) -> bool:
        """Whether the wallbox session already accounts for a vehicle that reports charging.

        Only a vehicle at home can be at the wallbox. Once the wallbox session
        names another vehicle, this one is a different car. While it names
        none, the vehicle counts as the car at the wallbox when its charging
        report, made at the given moment, falls in the window of the wallbox
        session and its power does not contradict the wallbox power. A wallbox
        session that began after the report is in the window. The verdict
        holds until that session ends. It assigns nothing: the wallbox session
        stays as it is.
        """
        session = self._session
        vehicle_id = context.vehicle.id
        if session is None or self._vehicle_location(context) != TRACKER_STATE_HOME:
            return False
        if session.vehicle_id is not None:
            return False
        if vehicle_id in session.same_vehicles:
            return True
        edges = [session.power_since, session.pause_since]
        if session.phases:
            edges += [_parse(session.phases[-1].start), _parse(session.phases[-1].end)]
        recent = [edge for edge in edges if edge is not None]
        charging = self._power_active()
        matches = is_wallbox_vehicle(
            session_age_s=(now - session.start).total_seconds(),
            charge_edge_age_s=(now - max(recent)).total_seconds() if recent else None,
            wallbox_charging=charging,
            wallbox_power_kw=self._power_kw if charging else None,
            vehicle_power_kw=self._read_vehicle_number(
                context, ROLE_CHARGE_POWER, POWER_UNIT_FACTORS_TO_KW
            ),
        )
        if matches:
            session.same_vehicles.append(vehicle_id)
            self._persist()
        return matches

    def _arm_vehicle_rearm(self, session: RunningSession) -> None:
        """Hold back vehicles of an ended wallbox session that still report charging.

        A vehicle reports the unplugging late, so it may go on reporting
        charging for a while. It may begin its own session again only after
        it reported something else.
        """
        for vehicle_id in {*session.same_vehicles, session.vehicle_id} - {None}:
            if self._vehicle_charge_class.get(vehicle_id) == CHARGE_STATE_CHARGING:
                self._vehicle_rearm.add(vehicle_id)

    @callback
    def _on_vehicle_plug_state(self, context: VehicleContext, state: State | None) -> None:
        """Classify a vehicle's plug state; not connected ends its own session.

        The plug state only ever ends a session. A value the mapping marks
        neutral keeps the last class, and an unusable state changes nothing.
        """
        vehicle_id = context.vehicle.id
        raw = resolver.usable_state(state)
        if raw is None:
            return
        mapping = context.mapping.role_values(ROLE_PLUG_STATE) if context.mapping else {}
        klass, found = resolver.classify_with_neutral(
            raw,
            mapping,
            default=PLUG_STATE_CONNECTED,
            last_class=self._vehicle_plug_class.get(vehicle_id),
        )
        problems.check_unknown_mapping_value(
            self._hass,
            found=found,
            subentry_id=context.subentry_id,
            subentry_title=context.title,
            role_name=ROLE_PLUG_STATE,
            raw_value=raw,
        )
        if klass is not None:
            self._vehicle_plug_class[vehicle_id] = klass
        session = self._vehicle_sessions.get(vehicle_id)
        if klass == PLUG_STATE_NOT_CONNECTED:
            self._cancel_vehicle_pending(vehicle_id)
            if session is not None and session.state != SESSION_STATE_AWAITING_FINAL:
                self._end_vehicle_session(context, session, self._now())
        self._touch_live()

    def _enter_vehicle_state(self, session: RunningVehicleSession, state: str) -> None:
        """Record a new state of a vehicle's own session, persist it and publish at once (I12)."""
        if session.state != state or session.state_since is None:
            session.state_since = self._now()
        if session.state != state:
            _LOGGER.debug(
                "External session of vehicle %s: %s -> %s", session.vehicle_id, session.state, state
            )
        session.state = state
        self._persist()
        self._publish()

    @callback
    def _on_vehicle_pause_timer(self, context: VehicleContext) -> None:
        """Close a vehicle's open phase once the interruption reached the minimum pause."""
        self._timers.pop(self._vehicle_pause_timer_name(context.vehicle.id), None)
        session = self._vehicle_sessions.get(context.vehicle.id)
        if session is not None and session.state == SESSION_STATE_PAUSED and session.pause_since:
            self._close_vehicle_phase(session, session.pause_since)
            self._persist()

    def _open_vehicle_phase(self, session: RunningVehicleSession, now: datetime) -> None:
        """Start a new phase of a vehicle's own session; external phases carry no energy (6.3)."""
        if len(session.phases) >= MAX_PHASES:
            session.phases = list(merge_shortest_pauses(tuple(session.phases), MAX_PHASES - 1))
            session.flagged = True
        session.phases.append(Phase(start=_iso(now)))
        _LOGGER.debug(
            "External session of vehicle %s: phase %d begins",
            session.vehicle_id,
            len(session.phases),
        )

    def _close_vehicle_phase(self, session: RunningVehicleSession, end: datetime) -> None:
        """Close the open phase of a vehicle's own session at the given moment."""
        phase = session.open_phase()
        if phase is None:
            return
        start = _parse(phase.start)
        duration = max((end - start).total_seconds() / 60, 0.0) if start else 0.0
        session.phases[-1] = replace(phase, end=_iso(end), duration_min=duration)

    def _end_vehicle_session(
        self, context: VehicleContext, session: RunningVehicleSession, now: datetime
    ) -> None:
        """React to a vehicle's own charge state falling to disconnected, the only end (7.5)."""
        self._cancel_vehicle_timers(context.vehicle.id)
        end = session.pause_since if session.state == SESSION_STATE_PAUSED else now
        self._close_vehicle_phase(session, end)
        session.plug_end = now
        session.state = SESSION_STATE_AWAITING_FINAL
        session.state_since = self._now()
        self._persist()
        self._publish()
        self._hass.async_create_task(
            self._async_finalize_vehicle_session(context.vehicle.id), eager_start=False
        )

    @callback
    def _on_vehicle_stale_timer(self, context: VehicleContext) -> None:
        """Close a vehicle's own session after its source was unusable for the whole timeout."""
        self._timers.pop(self._vehicle_stale_timer_name(context.vehicle.id), None)
        session = self._vehicle_sessions.get(context.vehicle.id)
        if session is None or session.state == SESSION_STATE_AWAITING_FINAL:
            return
        self._cancel_timer(self._vehicle_pause_timer_name(context.vehicle.id))
        end = session.last_valid or session.start
        self._close_vehicle_phase(session, end)
        session.plug_end = end
        session.flagged = True
        session.state = SESSION_STATE_AWAITING_FINAL
        session.state_since = self._now()
        self._persist()
        self._publish()
        self._hass.async_create_task(
            self._async_finalize_vehicle_session(context.vehicle.id), eager_start=False
        )

    def _restore_vehicle_session_timers(self) -> None:
        """Re-arm the timers of every vehicle session restored from the store."""
        now = self._now()
        for vehicle_id, session in list(self._vehicle_sessions.items()):
            context = self._vehicles.get(vehicle_id)
            if context is None:
                continue
            if session.state == SESSION_STATE_AWAITING_FINAL:
                self._hass.async_create_task(
                    self._async_finalize_vehicle_session(vehicle_id), eager_start=False
                )
                continue
            if session.state == SESSION_STATE_PAUSED and session.pause_since:
                remaining = MIN_PAUSE_MIN * 60 - (now - session.pause_since).total_seconds()
                self._set_timer(
                    self._vehicle_pause_timer_name(vehicle_id),
                    remaining,
                    callback(lambda _now, c=context: self._on_vehicle_pause_timer(c)),
                )
            if session.unavailable_since:
                elapsed = (now - session.unavailable_since).total_seconds()
                self._set_timer(
                    self._vehicle_stale_timer_name(vehicle_id),
                    SESSION_TIMEOUT_H * 3600 - elapsed,
                    callback(lambda _now, c=context: self._on_vehicle_stale_timer(c)),
                )

    # ------------------------------------------------------------- geocoding

    def _start_geocode(self, vehicle_id: str, session_start: datetime) -> None:
        """Look up the address of a newly started external session, without waiting for it."""
        settings = self._settings
        if not settings.geocoding_enabled or not settings.geocoding_contact:
            return
        self._hass.async_create_task(
            self._async_geocode(vehicle_id, session_start), eager_start=False
        )

    async def _async_geocode(self, vehicle_id: str, session_start: datetime) -> None:
        """Resolve the address of a vehicle's running session and apply it if still current."""
        session = self._vehicle_sessions.get(vehicle_id)
        if session is None or session.latitude is None or session.longitude is None:
            return
        settings = self._settings
        address = await geocoding.async_get_queue(self._hass).async_lookup(
            self._hass,
            url=settings.geocoding_url,
            contact=settings.geocoding_contact,
            latitude=session.latitude,
            longitude=session.longitude,
        )
        session = self._vehicle_sessions.get(vehicle_id)
        if session is None or session.start != session_start:
            return
        if address is not None:
            session.address = address
            session.address_retry_pending = False
        self._persist()
        self._touch_live()

    async def _async_retry_pending_addresses(self) -> None:
        """Retry the address of every stored session still waiting for one, once at startup."""
        settings = self._settings
        if not settings.geocoding_enabled or not settings.geocoding_contact:
            return
        for year in await async_list_session_years(self._hass):
            store = SessionYearStore(self._hass, year)
            pending = [
                stored
                for stored in await store.async_load()
                if stored.address_retry_pending
                and stored.latitude is not None
                and stored.longitude is not None
            ]
            for target in pending:
                address = await geocoding.async_get_queue(self._hass).async_lookup(
                    self._hass,
                    url=settings.geocoding_url,
                    contact=settings.geocoding_contact,
                    latitude=target.latitude,
                    longitude=target.longitude,
                )
                if address is None:
                    continue

                def _apply(
                    sessions: list[Session], target_id: str = target.id, address: str = address
                ) -> list[Session]:
                    return [
                        replace(
                            s,
                            address=address,
                            address_retry_pending=False,
                            modified_at=_iso(self._now()),
                        )
                        if s.id == target_id
                        else s
                        for s in sessions
                    ]

                await store.async_update(_apply)

    # ------------------------------------------------------------ finishing

    def _counter_readable(self, session: RunningSession) -> bool:
        """Whether the energy counter was read from the start and can be read now."""
        assert self.wallbox is not None
        counter = session.counters.get(session.authoritative)
        if counter is None or counter.start_value is None or counter.started_late:
            return False
        role = (
            self.wallbox.energy_total
            if session.authoritative == COUNTER_TOTAL
            else self.wallbox.energy_session
        )
        entity_id = resolver.resolve_entity_id(self._hass, role)
        state = self._hass.states.get(entity_id) if entity_id else None
        return resolver.read_number(state, role, ENERGY_UNIT_FACTORS_TO_KWH) is not None

    def _is_empty(self, session: RunningSession, *, ended_by_unplug: bool) -> bool:
        """Whether the ended session holds nothing and is dropped instead of stored."""
        return should_discard(
            ended_by_unplug=ended_by_unplug,
            counter_readable=self._counter_readable(session),
            counter_increased=any(counter.accumulated > 0 for counter in session.counters.values()),
            phase_begun=bool(session.phases),
            charge_error=session.charge_error,
            flagged=session.flagged,
            identification_conflict=session.identification_conflict,
        )

    async def _async_finalize(self, *, stale: bool) -> None:
        """Turn the running session into a stored session, or drop it if it holds nothing."""
        session = self._session
        if session is None or self._finalizing:
            return
        self._finalizing = True
        empty = self._is_empty(session, ended_by_unplug=not stale)
        _LOGGER.debug(
            "The session ends: %d phases, %s",
            len(session.phases),
            "it holds nothing and is not stored" if empty else "it is stored",
        )
        try:
            if not empty:
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
        self._arm_vehicle_rearm(session)
        self._session = None
        if not empty:
            self._open_followups = await self._async_count_followups()
        await self._async_persist()
        self._publish()
        self._maybe_start_candidate(self._now())

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

    async def _async_finalize_vehicle_session(self, vehicle_id: str) -> None:
        """Write a finished vehicle session to the store, retrying on failure.

        The session stays in self._vehicle_sessions, in state
        awaiting_final, until the write succeeds, so a new charging report
        for the same vehicle in the meantime cannot resume it: only the
        disconnected class ever reaches here, and a session begins only from
        no session at all (I17).
        """
        session = self._vehicle_sessions.get(vehicle_id)
        context = self._vehicles.get(vehicle_id)
        if session is None or context is None or session.state != SESSION_STATE_AWAITING_FINAL:
            return
        if (
            session.address_retry_pending
            and session.latitude is not None
            and session.longitude is not None
        ):
            settings = self._settings
            if settings.geocoding_enabled and settings.geocoding_contact:
                address = await geocoding.async_get_queue(self._hass).async_lookup(
                    self._hass,
                    url=settings.geocoding_url,
                    contact=settings.geocoding_contact,
                    latitude=session.latitude,
                    longitude=session.longitude,
                )
                if address is not None:
                    session.address = address
                    session.address_retry_pending = False

        stored = self._build_vehicle_session(context, session)
        year = dt_util.as_local(session.start).year

        def _add(sessions: list[Session]) -> list[Session]:
            taken = {existing.id for existing in sessions}
            unique = stored
            counter = 2
            while unique.id in taken:
                unique = replace(stored, id=f"{stored.id}_{counter}")
                counter += 1
            return [*sessions, unique]

        try:
            await SessionYearStore(self._hass, year).async_update(_add)
        except Exception:
            _LOGGER.exception(
                "A finished external session could not be stored; it is kept and retried"
            )
            self._set_timer(
                f"vehicle_final_{vehicle_id}",
                60,
                callback(
                    lambda _now, v=vehicle_id: self._hass.async_create_task(
                        self._async_finalize_vehicle_session(v), eager_start=False
                    )
                ),
            )
            return
        del self._vehicle_sessions[vehicle_id]
        self._open_followups = await self._async_count_followups()
        await self._async_persist()
        self._publish()

    def _build_vehicle_session(
        self, context: VehicleContext, session: RunningVehicleSession
    ) -> Session:
        """Assemble the stored session from a vehicle's own running one (6.2, 7.4, 8.5).

        Cost is never determined for a session the wallbox did not capture:
        there is no readable price, so it always stays open for manual entry.
        """
        vehicle = context.vehicle
        phases = merge_shortest_pauses(tuple(session.phases), MAX_PHASES)
        flagged = session.flagged or len(phases) < len(session.phases)
        plug_end = session.plug_end or self._now()
        plug_duration = max((plug_end - session.start).total_seconds() / 60, 0.0)
        charge_duration = sum(phase.duration_min or 0.0 for phase in phases)
        pause_duration = max(plug_duration - charge_duration, 0.0)

        soc_end = self._read_vehicle_number(context, ROLE_SOC, None)
        capacity = vehicle.capacity_kwh
        raw_energy = energy_raw_kwh(session.soc_start, soc_end, capacity)
        # No efficiency factor is determined yet; the raw estimate stands in for it unfactored.
        estimated_energy = raw_energy
        energy_kwh = derive_energy_kwh(None, None, session.energy_session_kwh, estimated_energy)
        estimate_uncertain = (
            session.soc_start is not None
            and soc_end is not None
            and abs(soc_end - session.soc_start) < self._settings.estimate_uncertain_threshold_pct
        )

        charge_type = session.charge_type
        charge_type_source = session.charge_type_source
        if charge_type_source != CHARGE_TYPE_SOURCE_ENTITY:
            if energy_kwh is not None and charge_duration > 0:
                avg_kw = energy_kwh / (charge_duration / 60)
                charge_type = (
                    CURRENT_TYPE_DC if avg_kw >= DC_POWER_THRESHOLD_KW else CURRENT_TYPE_AC
                )
                charge_type_source = CHARGE_TYPE_SOURCE_HEURISTIC
            else:
                charge_type = CHARGE_TYPE_UNKNOWN
                charge_type_source = None

        open_fields: list[str] = []
        if session.soc_start is None:
            open_fields.append("soc_start")
        if soc_end is None:
            open_fields.append("soc_end")
        if session.odometer_km is None:
            open_fields.append("odometer_km")
        if energy_kwh is None:
            open_fields.append("energy_kwh")
        # Neither location carries a readable price; cost is always nacherfassbar (8.5).
        open_fields.append("cost")

        status = SESSION_STATUS_FLAGGED if flagged else SESSION_STATUS_FOLLOWUP_OPEN
        now_iso = _iso(self._now())
        start_local = dt_util.as_local(session.start)

        return Session(
            id=f"{start_local.strftime('%Y-%m-%dT%H:%M:%S')}_{vehicle.id}",
            location=session.location,
            plug_start=_iso(session.start),
            identification_source=IDENTIFICATION_SOURCE_VEHICLE_API,
            vehicle_id=vehicle.id,
            vehicle_name=vehicle.name,
            capacity_kwh=capacity,
            wallbox_id=None,
            plug_end=_iso(plug_end),
            plug_duration_min=round(plug_duration, 1),
            charge_duration_min=round(charge_duration, 1),
            pause_duration_min=round(pause_duration, 1),
            phase_count=len(phases),
            phases_recorded=True,
            soc_start=session.soc_start,
            soc_end=soc_end,
            odometer_km=session.odometer_km,
            energy_vehicle_kwh=_round(session.energy_session_kwh, 3),
            energy_raw_kwh=_round(raw_energy, 3),
            energy_estimated_kwh=_round(estimated_energy, 3),
            energy_kwh=_round(energy_kwh, 3),
            estimate_uncertain=estimate_uncertain,
            charge_type=charge_type,
            charge_type_source=charge_type_source,
            power_avg_kw=(
                round(energy_kwh / (charge_duration / 60), 2)
                if energy_kwh is not None and charge_duration > 0
                else None
            ),
            address=session.address,
            latitude=session.latitude,
            longitude=session.longitude,
            location_reported_at=(
                _iso(session.location_reported_at) if session.location_reported_at else None
            ),
            address_retry_pending=session.address_retry_pending,
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
        payload: dict[str, Any] = {
            "session": self._session.to_dict() if self._session else None,
            "vehicle_sessions": {
                vehicle_id: session.to_dict()
                for vehicle_id, session in self._vehicle_sessions.items()
            },
        }
        if self._counter_detection is not None:
            payload["counter_detection"] = self._counter_detection
        if self._vehicle_rearm:
            payload["vehicle_rearm"] = sorted(self._vehicle_rearm)
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
        if session.state != SESSION_STATE_AWAITING_FINAL:
            assert self._card_reader is not None
            if session.card_uid is None:
                self._begin_identification(session)
                if session.phases:
                    self._card_reader.begin_charging()
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
        """Rebuild and publish the snapshots, and refresh the live subscribers."""
        self.snapshot = self._build_snapshot()
        self.vehicle_snapshots = self._build_vehicle_snapshots()
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

    def _net_duration_min(
        self, session: RunningSession | RunningVehicleSession, now: datetime
    ) -> float:
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

    def _vehicle_session_energy(
        self, context: VehicleContext, session: RunningVehicleSession
    ) -> tuple[float | None, bool]:
        """Return a vehicle's own session energy, and whether it is only an estimate (8.4).

        The vehicle's reported session energy is authoritative where present;
        without it, energy is estimated from the state of charge alone.
        """
        if session.energy_session_kwh is not None:
            return session.energy_session_kwh, False
        soc = self._read_vehicle_number(context, ROLE_SOC, None)
        estimate = energy_raw_kwh(session.soc_start, soc, context.vehicle.capacity_kwh)
        return estimate, estimate is not None

    def _vehicle_charge_end(self, context: VehicleContext) -> datetime | None:
        """Return a vehicle's own reported charge end, normalized to a timestamp."""
        entity_id = resolver.resolve_entity_id(self._hass, context.vehicle.charge_end)
        raw_end = resolver.usable_state(self._hass.states.get(entity_id)) if entity_id else None
        charge_end = dt_util.parse_datetime(raw_end) if raw_end else None
        return dt_util.as_utc(charge_end) if charge_end is not None else None

    def _build_vehicle_snapshots(self) -> dict[str, VehicleSnapshot]:
        """Collect what every vehicle's own entities publish (11.4, 11.5)."""
        now = self._now()
        snapshots: dict[str, VehicleSnapshot] = {}
        for vehicle_id, context in self._vehicles.items():
            session = self._vehicle_sessions.get(vehicle_id)
            active = session is not None and session.state != SESSION_STATE_AWAITING_FINAL
            energy = self._vehicle_session_energy(context, session)[0] if active else None
            snapshots[vehicle_id] = VehicleSnapshot(
                session_active=active,
                session_state=session.state if active else None,
                session_location=session.location if active else None,
                session_soc_start=session.soc_start if active else None,
                session_odometer_start=session.odometer_km if active else None,
                session_energy_kwh=round(energy, 3) if energy is not None else None,
                session_duration_net_min=(
                    round(self._net_duration_min(session, now), 1) if active else None
                ),
                charge_end=self._vehicle_charge_end(context),
            )
        return snapshots

    def _plug_report(self, session: RunningSession | None) -> dict[str, Any]:
        """Describe the plug state of the wallbox for the live card."""
        unusable = not self._plug_usable or self._plug_class is None
        since = session.plug_unavailable_since if session is not None else None
        timeout_at = since + timedelta(hours=SESSION_TIMEOUT_H) if since is not None else None
        return {
            "state": PLUG_REPORT_UNAVAILABLE if unusable else self._plug_class,
            "unavailable_since": _iso(since) if since is not None and unusable else None,
            "timeout_at": _iso(timeout_at) if timeout_at is not None and unusable else None,
        }

    def _configured_counter(self) -> str:
        """Return the counter that carries the energy according to the setup."""
        assert self.wallbox is not None
        return COUNTER_TOTAL if self.wallbox.energy_total is not None else COUNTER_SESSION

    def live_payload(self) -> dict[str, Any]:
        """Return the live values of the wallbox's own session, or its idle state."""
        return self._wallbox_block()

    def live_blocks(self) -> list[dict[str, Any]]:
        """Return the live values of every running session (11.1, E34, E37).

        The wallbox block comes first, even without a session there, so the
        card always has a fixed anchor; the running external sessions follow
        it in the order they began. Card identifiers, VIN and coordinates are
        never included; the address is (14).
        """
        blocks = [self._wallbox_block()]
        running = [
            (self._vehicles[vehicle_id], session)
            for vehicle_id, session in self._vehicle_sessions.items()
            if session.state != SESSION_STATE_AWAITING_FINAL and vehicle_id in self._vehicles
        ]
        running.sort(key=lambda item: item[1].start)
        blocks.extend(self._vehicle_block(context, session) for context, session in running)
        return blocks

    def _wallbox_block(self) -> dict[str, Any]:
        """Return the live block of the wallbox's own session, or its idle state."""
        assert self.wallbox is not None
        assert self._card_reader is not None
        session = self._session
        now = self._now()
        context = self._vehicle_context()
        snapshot = self._build_snapshot()
        energy = None
        if session is not None:
            counter = session.counters.get(session.authoritative)
            if counter is not None and counter.start_value is not None:
                energy = round(counter.accumulated, 3)
        progress = self._card_reader.progress if session is not None else None
        # A vehicle keeps reporting its last expected charge end while it does not charge.
        charge_end = snapshot.vehicle_charge_end
        charge_end_missing = None
        if (
            context is not None
            and context.vehicle.charge_end is not None
            and snapshot.state != SESSION_STATE_CHARGING
        ):
            charge_end = None
            charge_end_missing = CHARGE_END_MISSING_NO_POWER
        return {
            "kind": LIVE_BLOCK_WALLBOX,
            "state": snapshot.state,
            "state_since": _iso(session.state_since) if session and session.state_since else None,
            "active": session is not None,
            "phase_count": len(session.phases) if session else 0,
            "waiting_for_power": bool(
                session and session.state == SESSION_STATE_PAUSED and not session.phases
            ),
            "plug": self._plug_report(session),
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
            "identification_conflict": bool(session and session.identification_conflict),
            "identification_read": (
                {
                    "state": progress.state,
                    "sequence": progress.sequence,
                    "attempt": progress.attempt,
                    "max_attempts": progress.max_attempts,
                }
                if progress is not None
                else None
            ),
            "location": LOCATION_HOME if session else None,
            "address": None,
            "soc_start": snapshot.soc_start,
            "soc": snapshot.vehicle_soc,
            "soc_target": snapshot.vehicle_soc_target,
            "odometer_km": snapshot.odometer_start,
            "range_km": None,
            "charge_type": None,
            "charge_end": charge_end.isoformat() if charge_end else None,
            "charge_end_missing": charge_end_missing,
            "charge_power_kw": self._power_kw,
            "energy_kwh": energy,
            "energy_is_estimate": False,
            "energy_grid_kwh": snapshot.energy_grid_kwh,
            "energy_solar_kwh": snapshot.energy_solar_kwh,
            "grid_share_pct": snapshot.grid_share_pct,
            "cost": snapshot.cost,
            "effective_price": snapshot.effective_price,
            "net_duration_min": snapshot.duration_net_min,
            "plug_duration_min": (
                round((now - session.start).total_seconds() / 60, 1) if session else None
            ),
            "energy_unallocated_kwh": round(session.unallocated_kwh, 3) if session else None,
            "counter": {
                "authoritative": session.authoritative if session else None,
                "switched": bool(session and session.authoritative != self._configured_counter()),
            },
            "sources": {
                "grid_balance": self._grid_configured(),
                "grid_price": self._prices_configured(),
            },
            "flagged": bool(session and session.flagged),
            "charge_error": bool(session and session.charge_error),
            "location_conflict": bool(session and session.location_conflict),
        }

    def _vehicle_block(
        self, context: VehicleContext, session: RunningVehicleSession
    ) -> dict[str, Any]:
        """Return the live block of a vehicle's own running session (11.1, E37)."""
        vehicle = context.vehicle
        now = self._now()
        soc = self._read_vehicle_number(context, ROLE_SOC, None)
        soc_target = self._read_vehicle_number(context, ROLE_SOC_TARGET, None)
        range_km = self._read_vehicle_number(context, ROLE_RANGE, DISTANCE_UNIT_FACTORS_TO_KM)
        charge_power = self._read_vehicle_number(
            context, ROLE_CHARGE_POWER, POWER_UNIT_FACTORS_TO_KW
        )
        charge_end = self._vehicle_charge_end(context)
        energy, energy_is_estimate = self._vehicle_session_energy(context, session)
        return {
            "kind": LIVE_BLOCK_EXTERNAL,
            "state": session.state,
            "state_since": _iso(session.state_since) if session.state_since else None,
            "active": True,
            "phase_count": len(session.phases),
            "waiting_for_power": False,
            "plug": None,
            "wallbox": None,
            "currency": self._hass.config.currency,
            "session_start": _iso(session.start),
            "vehicle": {"id": vehicle.id, "name": vehicle.name},
            "vehicle_guest": vehicle.is_guest,
            "identification_source": IDENTIFICATION_SOURCE_VEHICLE_API,
            "identification_decided": True,
            "identification_conflict": False,
            "identification_read": None,
            "location": session.location,
            "address": session.address,
            "soc_start": session.soc_start,
            "soc": soc,
            "soc_target": soc_target,
            "odometer_km": session.odometer_km,
            "range_km": range_km,
            "charge_type": session.charge_type
            if session.charge_type != CHARGE_TYPE_UNKNOWN
            else None,
            "charge_end": charge_end.isoformat() if charge_end else None,
            "charge_end_missing": None,
            "charge_power_kw": charge_power,
            "energy_kwh": round(energy, 3) if energy is not None else None,
            "energy_is_estimate": energy_is_estimate,
            "energy_grid_kwh": None,
            "energy_solar_kwh": None,
            "grid_share_pct": None,
            "cost": None,
            "effective_price": None,
            "net_duration_min": round(self._net_duration_min(session, now), 1),
            "plug_duration_min": round((now - session.start).total_seconds() / 60, 1),
            "energy_unallocated_kwh": None,
            "counter": None,
            "sources": None,
            "flagged": session.flagged,
            "charge_error": session.charge_error,
            "location_conflict": False,
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


# --------------------------------------------------------------------------
# Corrections and nacherfassung on stored sessions (10, 13, 15). Both the
# services and the panel's WebSocket commands call these functions, so there
# is exactly one place that changes a stored session by hand.


class SessionOperationError(Exception):
    """Base class for a rejected session correction."""


class SessionNotFoundError(SessionOperationError):
    """No stored session has the given id."""

    def __init__(self, session_id: str) -> None:
        """Keep the id that was not found."""
        super().__init__(f"No session with id {session_id}")
        self.session_id = session_id


class SessionValidationError(SessionOperationError):
    """The requested change is not valid for this session."""


class SessionMergeError(SessionValidationError):
    """The selected sessions do not meet the conditions for merging."""

    def __init__(self, check: MergeCheck) -> None:
        """Keep the failed check, so the caller can name every unmet condition."""
        super().__init__(f"Sessions cannot be merged: {', '.join(check.violations)}")
        self.check = check


def parse_offset_datetime(value: str) -> datetime:
    """Parse an ISO 8601 timestamp that carries a UTC offset (6.4).

    Raises ValueError if value is not a timestamp or carries no offset.
    """
    parsed = dt_util.parse_datetime(value)
    if parsed is None or parsed.tzinfo is None:
        raise ValueError("expected an ISO 8601 timestamp with a UTC offset")
    return parsed


def _history_state(hass: HomeAssistant, entity_id: str, at: datetime) -> State | None:
    """Blocking: the entity's state in effect at the given moment (recorder history).

    Returns None on any failure, including a recorder that is not loaded at
    all: a missing history is treated the same as one with no answer, never
    as a fault of this integration.
    """
    try:
        changes = history.state_changes_during_period(
            hass, at, at, entity_id, include_start_time_state=True, no_attributes=False
        )
    except Exception:
        _LOGGER.debug("Recorder history for %s is not available", entity_id, exc_info=True)
        return None
    states = changes.get(entity_id) or []
    return states[0] if states else None


async def async_role_history_number(
    hass: HomeAssistant,
    role: EntityRole | None,
    at: datetime,
    factors: dict[str, float] | None,
) -> float | None:
    """Read a numeric role's recorded value at a point in time (7.8), executor-only."""
    entity_id = resolver.resolve_entity_id(hass, role)
    if entity_id is None:
        return None
    state = await hass.async_add_executor_job(_history_state, hass, entity_id, at)
    return resolver.read_number(state, role, factors)


def _hub_settings(hass: HomeAssistant) -> HubSettings | None:
    """Return the global settings of the loaded hub entry, if there is one."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return HubSettings.from_dict(entry.data)
    return None


def _estimate_uncertain_threshold(hass: HomeAssistant) -> float:
    """Return the configured threshold, or the default if no hub entry is loaded."""
    settings = _hub_settings(hass)
    return (
        settings.estimate_uncertain_threshold_pct
        if settings is not None
        else DEFAULT_ESTIMATE_UNCERTAIN_THRESHOLD_PCT
    )


def _vehicle_by_id(hass: HomeAssistant, vehicle_id: str) -> Vehicle | None:
    """Return the configured vehicle with the given id, if any."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        for subentry in entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_VEHICLE:
                vehicle = Vehicle.from_dict(subentry.data)
                if vehicle.id == vehicle_id:
                    return vehicle
    return None


def _first_wallbox(hass: HomeAssistant) -> Wallbox | None:
    """Return the configured wallbox, if any. At most one is allowed (E1)."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        for subentry in entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_WALLBOX:
                return Wallbox.from_dict(subentry.data)
    return None


async def async_find_stored_session(hass: HomeAssistant, session_id: str) -> tuple[int, Session]:
    """Return the year and the stored session for a session id.

    Raises SessionNotFoundError if no year holds a session with that id.
    """
    for year in await async_list_session_years(hass):
        for session in await SessionYearStore(hass, year).async_load():
            if session.id == session_id:
                return year, session
    raise SessionNotFoundError(session_id)


async def _async_replace_session(hass: HomeAssistant, year: int, updated: Session) -> None:
    """Overwrite one stored session of a year by id."""

    def _apply(sessions: list[Session]) -> list[Session]:
        return [updated if session.id == updated.id else session for session in sessions]

    await SessionYearStore(hass, year).async_update(_apply)


async def _async_refresh_followups(hass: HomeAssistant) -> None:
    """Tell every loaded manager to recount open follow-ups after a stored session changed."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED and entry.runtime_data.manager is not None:
            await entry.runtime_data.manager.async_refresh_followups()


_OPEN_FIELD_ORDER = ("vehicle_id", "soc_start", "soc_end", "odometer_km", "energy_kwh", "cost")


def _sync_open_fields(session: Session, candidates: tuple[str, ...]) -> Session:
    """Add or remove open_fields entries among candidates, from their current values.

    Only the given candidates are touched: each is present exactly while its
    value is still null. A field a correction never writes, such as cost on
    a home session with no configured grid price, is never turned into an
    open field just because it happens to be null; every other existing
    entry is left exactly as it was.
    """
    fields = set(session.open_fields)
    for name in candidates:
        if getattr(session, name) is None:
            fields.add(name)
        else:
            fields.discard(name)
    ordered = tuple(name for name in _OPEN_FIELD_ORDER if name in fields)
    extra = tuple(name for name in fields if name not in _OPEN_FIELD_ORDER)
    return replace(session, open_fields=(*ordered, *extra))


def _recompute_status(session: Session) -> Session:
    """Promote followup_open to complete once nothing is missing; flagged always persists."""
    if session.status == SESSION_STATUS_FLAGGED:
        return session
    status = SESSION_STATUS_FOLLOWUP_OPEN if session.open_fields else SESSION_STATUS_COMPLETE
    return replace(session, status=status)


def _recompute_energy(session: Session, *, threshold_pct: float) -> Session:
    """Recompute the fields derived from soc_start, soc_end, capacity_kwh and energy_billed_kwh.

    No efficiency factor exists yet (Kapitel 9 is a later stage); the raw
    estimate stands in for it unfactored, the same as the live capture.
    """
    raw = energy_raw_kwh(session.soc_start, session.soc_end, session.capacity_kwh)
    energy_kwh = derive_energy_kwh(
        session.energy_billed_kwh, session.energy_measured_kwh, session.energy_vehicle_kwh, raw
    )
    power_avg = (
        round(energy_kwh / (session.charge_duration_min / 60), 2)
        if energy_kwh is not None and session.charge_duration_min
        else None
    )
    uncertain = (
        session.soc_start is not None
        and session.soc_end is not None
        and abs(session.soc_end - session.soc_start) < threshold_pct
    )
    return replace(
        session,
        energy_raw_kwh=_round(raw, 3),
        energy_estimated_kwh=_round(raw, 3),
        energy_kwh=_round(energy_kwh, 3),
        power_avg_kw=power_avg,
        estimate_uncertain=uncertain,
    )


def _add_modified(session: Session, *names: str) -> Session:
    """Append field names to modified_fields, without duplicates."""
    modified = list(session.modified_fields)
    for name in names:
        if name not in modified:
            modified.append(name)
    return replace(session, modified_fields=tuple(modified))


async def async_update_session(
    hass: HomeAssistant, session_id: str, values: dict[str, Any]
) -> Session:
    """Apply a nacherfassung or correction to one stored session (10, 13, 15).

    values may hold any of UPDATE_SESSION_FIELDS from const.py; the caller's
    schema rejects anything else before this runs. charge_type is only
    accepted for a session whose charge_type_source is heuristic (5.5), and
    plug_end only while it is still unset.
    """
    year, session = await async_find_stored_session(hass, session_id)

    changes: dict[str, Any] = {}
    for name, value in values.items():
        if name == "charge_type" and session.charge_type_source != CHARGE_TYPE_SOURCE_HEURISTIC:
            raise SessionValidationError(
                "charge_type can only be corrected for a heuristically determined session"
            )
        if name == "plug_end":
            if session.plug_end is not None:
                raise SessionValidationError("plug_end is already set")
            try:
                plug_start = parse_offset_datetime(session.plug_start)
            except ValueError as err:
                raise SessionValidationError(
                    f"Session {session_id} has an unreadable plug_start"
                ) from err
            changes["plug_end"] = _iso(value)
            changes["plug_duration_min"] = round((value - plug_start).total_seconds() / 60, 1)
            continue
        changes[name] = value

    updated = replace(session, **changes, modified_at=_now_iso())
    updated = _add_modified(updated, *changes.keys())
    open_candidates = {name for name in changes if name in _OPEN_FIELD_ORDER}
    if {"soc_start", "soc_end", "energy_billed_kwh"} & changes.keys():
        updated = _recompute_energy(updated, threshold_pct=_estimate_uncertain_threshold(hass))
        open_candidates.add("energy_kwh")
    updated = _sync_open_fields(updated, tuple(open_candidates))
    updated = _recompute_status(updated)

    await _async_replace_session(hass, year, updated)
    await _async_refresh_followups(hass)
    return updated


async def async_delete_session(hass: HomeAssistant, session_id: str) -> None:
    """Remove one stored session (13)."""
    year, _ = await async_find_stored_session(hass, session_id)

    def _remove(sessions: list[Session]) -> list[Session]:
        return [session for session in sessions if session.id != session_id]

    await SessionYearStore(hass, year).async_update(_remove)
    await _async_refresh_followups(hass)


async def async_close_followup(hass: HomeAssistant, session_id: str) -> Session:
    """Accept a session's remaining missing values as final (10).

    open_fields is cleared; a status of followup_open is promoted to
    complete. A session that is flagged for another reason stays flagged.
    """
    year, session = await async_find_stored_session(hass, session_id)
    updated = replace(session, open_fields=(), modified_at=_now_iso())
    updated = _recompute_status(updated)
    await _async_replace_session(hass, year, updated)
    await _async_refresh_followups(hass)
    return updated


async def async_correct_vehicle(hass: HomeAssistant, session_id: str, vehicle_id: str) -> Session:
    """Reassign a stored session to a different vehicle, or resolve an unresolved one (7.8).

    energy, cost and phases are kept and now belong to the corrected
    vehicle. capacity_kwh is taken from the new vehicle. soc_start and
    odometer_km are re-read from the new vehicle's recorder history at
    plug_start; a value the recorder cannot supply goes to open_fields.
    soc_end is not re-determined, matching 7.8's correction table, which
    names only soc_start and odometer_km. card_uid and card_label are kept
    as the identification actually read, marked identification_corrected.
    """
    year, session = await async_find_stored_session(hass, session_id)
    vehicle = _vehicle_by_id(hass, vehicle_id)
    if vehicle is None:
        raise SessionValidationError(f"Unknown vehicle {vehicle_id}")

    try:
        plug_start = parse_offset_datetime(session.plug_start)
    except ValueError as err:
        raise SessionValidationError(f"Session {session_id} has an unreadable plug_start") from err

    soc_start = await async_role_history_number(hass, vehicle.soc, plug_start, None)
    odometer_km = await async_role_history_number(
        hass, vehicle.odometer, plug_start, DISTANCE_UNIT_FACTORS_TO_KM
    )

    updated = replace(
        session,
        vehicle_id=vehicle.id,
        vehicle_name=vehicle.name,
        capacity_kwh=vehicle.capacity_kwh,
        soc_start=soc_start,
        odometer_km=odometer_km,
        identification_corrected=True,
        modified_at=_now_iso(),
    )
    updated = _add_modified(updated, "vehicle_id", "capacity_kwh", "soc_start", "odometer_km")
    updated = _recompute_energy(updated, threshold_pct=_estimate_uncertain_threshold(hass))
    updated = _sync_open_fields(updated, ("vehicle_id", "soc_start", "odometer_km", "energy_kwh"))
    updated = _recompute_status(updated)

    await _async_replace_session(hass, year, updated)
    await _async_refresh_followups(hass)
    return updated


def _now_iso() -> str:
    """Format the current moment as local ISO 8601 with offset, to the second."""
    return _iso(dt_util.utcnow())


def _local_year(session: Session) -> int:
    """Return the year a stored session belongs to: that of plug_start in local time."""
    try:
        return dt_util.as_local(parse_offset_datetime(session.plug_start)).year
    except ValueError as err:
        raise SessionValidationError(f"Session {session.id} has an unreadable plug_start") from err


async def async_merge_sessions(
    hass: HomeAssistant,
    session_ids: Sequence[str],
    odometer_inputs: dict[str, float],
    *,
    dry_run: bool = False,
) -> Session:
    """Replace the given stored sessions by one merged session.

    Only ever runs on an explicit request. odometer_inputs holds entered
    readings for sessions without odometer_km. Raises SessionNotFoundError
    for an unknown id and SessionMergeError if a condition is not met. With
    dry_run, the merged session is returned without writing anything.
    """
    ids = list(dict.fromkeys(session_ids))
    located = [await async_find_stored_session(hass, session_id) for session_id in ids]
    threshold = _estimate_uncertain_threshold(hass)
    modified_at = _now_iso()

    def _build(sources: list[Session]) -> Session:
        try:
            return merge_sessions(
                sources,
                odometer_inputs,
                local_year=_local_year,
                estimate_uncertain_threshold_pct=threshold,
                modified_at=modified_at,
            )
        except MergeRejectedError as err:
            raise SessionMergeError(err.check) from err

    preview = _build([session for _, session in located])
    if dry_run:
        return preview

    built: list[Session] = []

    def _apply(current: list[Session]) -> list[Session]:
        def _build_and_keep(sources: list[Session]) -> Session:
            built.append(_build(sources))
            return built[-1]

        try:
            return replace_by_merged(current, ids, _build_and_keep)
        except MissingSessionsError as err:
            raise SessionNotFoundError(str(err)) from err

    await SessionYearStore(hass, located[0][0]).async_update(_apply)
    await _async_refresh_followups(hass)
    _LOGGER.info("Merged %s sessions into %s", len(ids), built[-1].id)
    return built[-1]


async def async_create_session(hass: HomeAssistant, fields: dict[str, Any]) -> Session:
    """Fully reconstruct a past charging session by hand (13).

    Modeled on the legacy-data import (16): a single synthetic phase spans
    the whole plugged-in time, phases_recorded is false, and power_avg_kw is
    derived from energy and duration. No efficiency factor exists yet, so an
    energy estimate from the state of charge is used unfactored, the same as
    the live capture.
    """
    location = fields["location"]
    plug_start: datetime = fields["plug_start"]
    plug_end: datetime = fields["plug_end"]
    if plug_end <= plug_start:
        raise SessionValidationError("plug_end must be after plug_start")

    vehicle_id = fields.get("vehicle_id")
    vehicle = _vehicle_by_id(hass, vehicle_id) if vehicle_id else None
    if vehicle_id and vehicle is None:
        raise SessionValidationError(f"Unknown vehicle {vehicle_id}")

    plug_duration = (plug_end - plug_start).total_seconds() / 60
    soc_start = fields.get("soc_start")
    soc_end = fields.get("soc_end")
    capacity = vehicle.capacity_kwh if vehicle is not None else None
    raw = energy_raw_kwh(soc_start, soc_end, capacity)
    energy_kwh = derive_energy_kwh(fields.get("energy_billed_kwh"), None, None, raw)
    power_avg = (
        round(energy_kwh / (plug_duration / 60), 2)
        if energy_kwh is not None and plug_duration > 0
        else None
    )
    threshold = _estimate_uncertain_threshold(hass)
    estimate_uncertain = (
        soc_start is not None and soc_end is not None and abs(soc_end - soc_start) < threshold
    )

    charge_type = fields.get("charge_type")
    wallbox = _first_wallbox(hass) if location == LOCATION_HOME else None
    if charge_type is not None:
        charge_type_source: str | None = CHARGE_TYPE_SOURCE_HEURISTIC
    elif wallbox is not None:
        charge_type = wallbox.current_type
        charge_type_source = CHARGE_TYPE_SOURCE_WALLBOX_CONFIG
    else:
        charge_type = CHARGE_TYPE_UNKNOWN
        charge_type_source = None

    open_fields = tuple(
        name
        for name, value in (
            ("vehicle_id", vehicle_id),
            ("soc_start", soc_start),
            ("soc_end", soc_end),
            ("odometer_km", fields.get("odometer_km")),
            ("energy_kwh", energy_kwh),
            ("cost", fields.get("cost")),
        )
        if value is None
    )
    status = SESSION_STATUS_FOLLOWUP_OPEN if open_fields else SESSION_STATUS_COMPLETE

    now_iso = _now_iso()
    local_start = dt_util.as_local(plug_start)
    suffix = vehicle_id or IDENTIFICATION_SOURCE_UNRESOLVED
    base_id = f"{local_start.strftime('%Y-%m-%dT%H:%M:%S')}_{suffix}"
    phase = Phase(start=_iso(plug_start), end=_iso(plug_end), duration_min=round(plug_duration, 1))

    session = Session(
        id=base_id,
        location=location,
        plug_start=_iso(plug_start),
        identification_source=(
            IDENTIFICATION_SOURCE_MANUAL if vehicle_id else IDENTIFICATION_SOURCE_UNRESOLVED
        ),
        vehicle_id=vehicle_id,
        vehicle_name=vehicle.name if vehicle is not None else None,
        capacity_kwh=capacity,
        wallbox_id=wallbox.id if wallbox is not None else None,
        plug_end=_iso(plug_end),
        plug_duration_min=round(plug_duration, 1),
        charge_duration_min=round(plug_duration, 1),
        pause_duration_min=0.0,
        phase_count=1,
        phases_recorded=False,
        soc_start=soc_start,
        soc_end=soc_end,
        odometer_km=fields.get("odometer_km"),
        energy_billed_kwh=fields.get("energy_billed_kwh"),
        energy_raw_kwh=_round(raw, 3),
        energy_estimated_kwh=_round(raw, 3),
        energy_kwh=_round(energy_kwh, 3),
        estimate_uncertain=estimate_uncertain,
        cost=fields.get("cost"),
        charge_type=charge_type,
        charge_type_source=charge_type_source,
        power_avg_kw=power_avg,
        address=fields.get("address"),
        provider=fields.get("provider"),
        note=fields.get("note"),
        status=status,
        open_fields=open_fields,
        created_at=now_iso,
        modified_at=now_iso,
        phases=(phase,),
    )

    def _add(sessions: list[Session]) -> list[Session]:
        taken = {existing.id for existing in sessions}
        unique = session
        counter = 2
        while unique.id in taken:
            unique = replace(session, id=f"{session.id}_{counter}")
            counter += 1
        return [*sessions, unique]

    await SessionYearStore(hass, local_start.year).async_update(_add)
    await _async_refresh_followups(hass)
    return session
