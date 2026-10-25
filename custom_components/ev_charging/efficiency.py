"""Efficiency factors per vehicle and charge type, derived from the stored sessions.

A factor is the median of the proven energy (billed, else measured) over the
raw energy from the change of the state of charge. The raw energy never holds
a factor, so a factor never feeds into its own recomputation. The factors are
cached in their own store and recomputed after each newly stored session and
after all data was deleted. Nothing here applies a factor to a session.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from statistics import median
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    CHARGE_TYPE_SOURCE_HEURISTIC,
    CURRENT_TYPES,
    DOMAIN,
    EFFICIENCY_DEFAULT_FACTOR,
    EFFICIENCY_MIN_SAMPLES,
    SESSION_STATUS_FLAGGED,
)
from .models import Session
from .store import EfficiencyStore, SessionYearStore, async_list_session_years

_LOGGER = logging.getLogger(__name__)

_DATA_EFFICIENCY = "efficiency"


@dataclass(frozen=True)
class EfficiencyFactor:
    """The factor of one vehicle and charge type, and the number of data points behind it."""

    vehicle_id: str
    charge_type: str
    factor: float
    samples: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the store."""
        return {
            "vehicle_id": self.vehicle_id,
            "charge_type": self.charge_type,
            "factor": self.factor,
            "samples": self.samples,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EfficiencyFactor:
        """Deserialize from the store."""
        return cls(
            vehicle_id=data["vehicle_id"],
            charge_type=data["charge_type"],
            factor=float(data["factor"]),
            samples=int(data["samples"]),
        )


def efficiency_ratio(session: Session) -> float | None:
    """Return the proven over the raw energy of a session, None if it is no data point.

    Excluded are sessions without a vehicle or a definite charge type, with an
    uncertain estimate, with a heuristic charge type or flagged, and sessions
    without proven energy or without a positive raw energy.
    """
    if session.vehicle_id is None or session.charge_type not in CURRENT_TYPES:
        return None
    if (
        session.estimate_uncertain
        or session.charge_type_source == CHARGE_TYPE_SOURCE_HEURISTIC
        or session.status == SESSION_STATUS_FLAGGED
    ):
        return None
    proven = (
        session.energy_billed_kwh
        if session.energy_billed_kwh is not None
        else session.energy_measured_kwh
    )
    raw = session.energy_raw_kwh
    if proven is None or raw is None or raw <= 0:
        return None
    return proven / raw


def compute_factors(sessions: Iterable[Session]) -> list[EfficiencyFactor]:
    """Return the factor of every vehicle and charge type that has at least one data point.

    Below the minimum number of data points the default factor applies.
    """
    ratios: dict[tuple[str, str], list[float]] = {}
    for session in sessions:
        ratio = efficiency_ratio(session)
        if ratio is not None and session.vehicle_id is not None:
            ratios.setdefault((session.vehicle_id, session.charge_type), []).append(ratio)
    return [
        EfficiencyFactor(
            vehicle_id=vehicle_id,
            charge_type=charge_type,
            factor=(
                median(values)
                if len(values) >= EFFICIENCY_MIN_SAMPLES
                else EFFICIENCY_DEFAULT_FACTOR
            ),
            samples=len(values),
        )
        for (vehicle_id, charge_type), values in sorted(ratios.items())
    ]


class Efficiency:
    """The cached factors of the running integration and their store."""

    def __init__(
        self, hass: HomeAssistant, factors: Iterable[EfficiencyFactor], computed_at: str | None
    ) -> None:
        """Hold the loaded factors."""
        self._hass = hass
        self._store = EfficiencyStore(hass)
        self._factors = {(item.vehicle_id, item.charge_type): item for item in factors}
        self._computed_at = computed_at
        self._listeners: list[Callable[[], None]] = []
        self._lock = asyncio.Lock()
        self._tasks: set[asyncio.Task[None]] = set()

    def factor(self, vehicle_id: str, charge_type: str) -> float:
        """Return the factor of a vehicle and charge type, the default one without data."""
        found = self._factors.get((vehicle_id, charge_type))
        return found.factor if found is not None else EFFICIENCY_DEFAULT_FACTOR

    def as_dict(self) -> dict[str, Any]:
        """Return the cached factors and the moment they were computed."""
        return {
            "computed_at": self._computed_at,
            "factors": [item.to_dict() for item in self._factors.values()],
        }

    @callback
    def add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Call listener after each recomputation; returns the function that stops it."""
        self._listeners.append(listener)

        @callback
        def _remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _remove

    async def async_recompute(self) -> None:
        """Compute the factors from every stored session and cache them."""
        async with self._lock:
            sessions: list[Session] = []
            for year in await async_list_session_years(self._hass):
                sessions.extend(await SessionYearStore(self._hass, year).async_load())
            factors = compute_factors(sessions)
            computed_at = dt_util.now().replace(microsecond=0).isoformat()
            await self._store.async_save(
                {"computed_at": computed_at, "factors": [item.to_dict() for item in factors]}
            )
            self._factors = {(item.vehicle_id, item.charge_type): item for item in factors}
            self._computed_at = computed_at
        _LOGGER.debug("Recomputed %d efficiency factors", len(factors))
        for listener in list(self._listeners):
            listener()

    @callback
    def schedule_recompute(self) -> None:
        """Recompute in a task of its own; the caller does not wait for it."""
        task = self._hass.async_create_task(self._async_recompute_logged(), eager_start=False)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _async_recompute_logged(self) -> None:
        """Recompute; a failure keeps the previous factors and is logged."""
        try:
            await self.async_recompute()
        except Exception:
            _LOGGER.warning(
                "The efficiency factors could not be recomputed; the previous ones stay",
                exc_info=True,
            )

    async def async_stop(self) -> None:
        """Wait for a recomputation still running."""
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)


def _efficiency(hass: HomeAssistant) -> Efficiency | None:
    """Return the factors of the running integration, None while none are set up."""
    return hass.data.get(DOMAIN, {}).get(_DATA_EFFICIENCY)


async def async_setup(hass: HomeAssistant) -> None:
    """Load the cached factors; without a cache every factor is the default one."""
    if _efficiency(hass) is not None:
        return
    try:
        stored = await EfficiencyStore(hass).async_load()
        factors = [EfficiencyFactor.from_dict(item) for item in (stored or {}).get("factors", [])]
        computed_at = (stored or {}).get("computed_at")
    except Exception:
        _LOGGER.warning(
            "The cached efficiency factors could not be read; the default applies", exc_info=True
        )
        factors, computed_at = [], None
    hass.data.setdefault(DOMAIN, {})[_DATA_EFFICIENCY] = Efficiency(hass, factors, computed_at)


async def async_unload(hass: HomeAssistant) -> None:
    """Drop the factors of the running integration once a recomputation has finished."""
    efficiency = hass.data.get(DOMAIN, {}).pop(_DATA_EFFICIENCY, None)
    if efficiency is not None:
        await efficiency.async_stop()


def factor(hass: HomeAssistant, vehicle_id: str, charge_type: str) -> float:
    """Return the factor of a vehicle and charge type, the default one without data."""
    efficiency = _efficiency(hass)
    if efficiency is None:
        return EFFICIENCY_DEFAULT_FACTOR
    return efficiency.factor(vehicle_id, charge_type)


def as_dict(hass: HomeAssistant) -> dict[str, Any] | None:
    """Return the cached factors of the running integration, None while none are set up."""
    efficiency = _efficiency(hass)
    return efficiency.as_dict() if efficiency is not None else None


@callback
def add_listener(hass: HomeAssistant, listener: Callable[[], None]) -> CALLBACK_TYPE:
    """Call listener after each recomputation; returns the function that stops it."""
    efficiency = _efficiency(hass)
    if efficiency is None:
        return lambda: None
    return efficiency.add_listener(listener)


@callback
def schedule_recompute(hass: HomeAssistant) -> None:
    """Recompute the factors in a task of its own, if the integration is set up."""
    efficiency = _efficiency(hass)
    if efficiency is not None:
        efficiency.schedule_recompute()


async def async_recompute(hass: HomeAssistant) -> None:
    """Recompute the factors and wait for it, if the integration is set up."""
    efficiency = _efficiency(hass)
    if efficiency is not None:
        await efficiency.async_recompute()
