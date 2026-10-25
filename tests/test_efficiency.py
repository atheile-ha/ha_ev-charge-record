"""Tests for the efficiency factors and their diagnostic entities."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from unittest.mock import patch

import pytest
from custom_components.ev_charging import efficiency
from custom_components.ev_charging.const import (
    ATTR_CONFIRM,
    CHARGE_TYPE_SOURCE_ENTITY,
    CHARGE_TYPE_SOURCE_HEURISTIC,
    CHARGE_TYPE_SOURCE_WALLBOX_CONFIG,
    DOMAIN,
    SERVICE_CREATE_SESSION,
    SERVICE_DELETE_ALL_DATA,
    SESSION_STATUS_FLAGGED,
    SESSION_STATUS_FOLLOWUP_OPEN,
    STORE_KEY_EFFICIENCY,
    SUBENTRY_TYPE_VEHICLE,
)
from custom_components.ev_charging.diagnostics import async_get_config_entry_diagnostics
from custom_components.ev_charging.efficiency import (
    EfficiencyFactor,
    compute_factors,
    efficiency_ratio,
)
from custom_components.ev_charging.models import Session
from custom_components.ev_charging.store import EfficiencyStore, SessionYearStore
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import EntityCategory
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser

from tests.test_session_manager import (
    TIME_ZONE,
    TOTAL,
    _eqb,
    _glb,
    _set,
    _setup,
    _start_charging,
    _stored,
    _touch_year_file,
    _unplug,
)

# Proven over raw energy of five sessions; their median is 1.12.
RATIOS = (1.0, 1.1, 1.12, 1.2, 1.3)


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Give the test a private config dir: the years with data are read from disk."""
    return hass_tmp_config_dir


@pytest.fixture(autouse=True)
async def _time_zone(hass: HomeAssistant) -> None:
    """Use a fixed time zone."""
    await hass.config.async_set_time_zone(TIME_ZONE)


def _session(
    index: int,
    *,
    vehicle_id: str | None = "v001",
    charge_type: str = "ac",
    raw: float | None = 10.0,
    ratio: float = 1.12,
    **fields: Any,
) -> Session:
    """A stored home session whose measured energy is ratio times its raw energy."""
    values: dict[str, Any] = {
        "id": f"2026-05-{index + 1:02d}T10:00:00_{vehicle_id}",
        "location": "home",
        "plug_start": f"2026-05-{index + 1:02d}T10:00:00+02:00",
        "identification_source": "rfid",
        "vehicle_id": vehicle_id,
        "charge_type": charge_type,
        "charge_type_source": CHARGE_TYPE_SOURCE_WALLBOX_CONFIG,
        "energy_raw_kwh": raw,
        "energy_measured_kwh": round(ratio * 10.0, 3),
        "energy_estimated_kwh": raw,
    }
    values.update(fields)
    return Session(**values)


def _sessions(ratios: tuple[float, ...] = RATIOS, **fields: Any) -> list[Session]:
    return [_session(i, ratio=ratio, **fields) for i, ratio in enumerate(ratios)]


def _only(factors: list[EfficiencyFactor]) -> EfficiencyFactor:
    (factor,) = factors
    return factor


# ---------------------------------------------------------------- pure


def test_the_factor_is_the_median_of_proven_over_raw_energy() -> None:
    factor = _only(compute_factors(_sessions()))
    assert factor.vehicle_id == "v001"
    assert factor.charge_type == "ac"
    assert factor.samples == 5
    assert factor.factor == pytest.approx(1.12)


def test_below_five_data_points_the_factor_is_one() -> None:
    factor = _only(compute_factors(_sessions((1.2, 1.3, 1.25, 1.22))))
    assert factor.samples == 4
    assert factor.factor == 1.0


@pytest.mark.parametrize(
    "fields",
    [
        {"estimate_uncertain": True},
        {"charge_type_source": CHARGE_TYPE_SOURCE_HEURISTIC},
        {"status": SESSION_STATUS_FLAGGED},
    ],
    ids=["estimate_uncertain", "heuristic", "flagged"],
)
def test_excluded_sessions_are_no_data_point(fields: dict[str, Any]) -> None:
    sessions = _sessions()
    sessions[0] = replace(sessions[0], **fields)
    factor = _only(compute_factors(sessions))
    assert factor.samples == 4
    assert factor.factor == 1.0


def test_an_open_followup_still_counts() -> None:
    sessions = _sessions(status=SESSION_STATUS_FOLLOWUP_OPEN, open_fields=("odometer_km",))
    assert _only(compute_factors(sessions)).samples == 5


@pytest.mark.parametrize(
    "fields",
    [
        {"vehicle_id": None},
        {"charge_type": "unknown"},
        {"raw": None},
        {"raw": 0.0},
        {"raw": -5.0},
        {"energy_measured_kwh": None},
    ],
    ids=["no_vehicle", "unknown_type", "no_raw", "zero_raw", "negative_raw", "no_proven"],
)
def test_a_session_without_a_usable_ratio_is_no_data_point(fields: dict[str, Any]) -> None:
    assert efficiency_ratio(_session(0, **fields)) is None


def test_billed_energy_takes_precedence_over_measured() -> None:
    session = _session(0, ratio=1.0, energy_billed_kwh=12.5, charge_type="dc")
    assert efficiency_ratio(session) == pytest.approx(1.25)


def test_factors_are_segmented_by_vehicle_and_charge_type() -> None:
    sessions = [
        *_sessions(),
        *(
            _session(
                10 + i, ratio=1.05, charge_type="dc", charge_type_source=CHARGE_TYPE_SOURCE_ENTITY
            )
            for i in range(5)
        ),
        *(_session(20 + i, vehicle_id="v002", ratio=1.08) for i in range(6)),
    ]
    factors = {(item.vehicle_id, item.charge_type): item for item in compute_factors(sessions)}
    assert set(factors) == {("v001", "ac"), ("v001", "dc"), ("v002", "ac")}
    assert factors["v001", "ac"].factor == pytest.approx(1.12)
    assert factors["v001", "dc"].factor == pytest.approx(1.05)
    assert factors["v002", "ac"].factor == pytest.approx(1.08)
    assert factors["v002", "ac"].samples == 6


def test_the_factor_never_feeds_into_its_own_recomputation() -> None:
    """The estimate carrying a factor leaves the next factor unchanged; raw is the divisor."""
    sessions = _sessions()
    first = _only(compute_factors(sessions))
    factored = [
        replace(
            session,
            energy_estimated_kwh=session.energy_raw_kwh * first.factor,
            energy_kwh=session.energy_raw_kwh * first.factor,
        )
        for session in sessions
    ]
    assert _only(compute_factors(factored)) == first
    distorted = [replace(session, energy_estimated_kwh=999.0) for session in sessions]
    assert _only(compute_factors(distorted)) == first


# ---------------------------------------------------------------- in Home Assistant


def _vehicle_subentry_id(entry: MockConfigEntry, vehicle_id: str) -> str:
    return next(
        subentry.subentry_id
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_VEHICLE and subentry.data["id"] == vehicle_id
    )


def _entity_id(hass: HomeAssistant, entry: MockConfigEntry, vehicle_id: str, charge_type: str):
    unique_id = f"{_vehicle_subentry_id(entry, vehicle_id)}_efficiency_{charge_type}"
    return er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)


def _state(hass: HomeAssistant, entry: MockConfigEntry, vehicle_id: str, charge_type: str):
    entity_id = _entity_id(hass, entry, vehicle_id, charge_type)
    assert entity_id is not None
    return float(hass.states.get(entity_id).state)


async def _seed(hass: HomeAssistant, sessions: list[Session]) -> int:
    """Store sessions in this year's store before setup; returns the year."""
    year = dt_util.now().year
    sessions = [replace(s, plug_start=s.plug_start.replace("2026", str(year))) for s in sessions]
    await SessionYearStore(hass, year).async_save(sessions)
    await _touch_year_file(hass, year)
    return year


def _cache(*factors: EfficiencyFactor) -> dict[str, Any]:
    return {
        "version": 1,
        "minor_version": 1,
        "key": STORE_KEY_EFFICIENCY,
        "data": {
            "computed_at": "2026-10-01T10:00:00+02:00",
            "factors": [item.to_dict() for item in factors],
        },
    }


async def _charge_once(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    await _start_charging(hass, freezer)
    await _set(hass, TOTAL, "105.0", "kWh")
    await _unplug(hass, freezer)
    await hass.async_block_till_done()


async def test_without_a_cache_the_factor_is_one_and_nothing_is_computed_at_setup(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    await _seed(hass, _sessions())
    entry, _manager = await _setup(hass, vehicles=(_glb(),))

    assert _state(hass, entry, "v001", "ac") == 1.0
    assert _state(hass, entry, "v001", "dc") == 1.0
    assert STORE_KEY_EFFICIENCY not in hass_storage


async def test_the_cached_factors_are_shown_after_a_restart(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass_storage[STORE_KEY_EFFICIENCY] = _cache(EfficiencyFactor("v001", "ac", 1.121, 49))
    entry, _manager = await _setup(hass, vehicles=(_glb(),))

    assert _state(hass, entry, "v001", "ac") == pytest.approx(1.121)
    assert _state(hass, entry, "v001", "dc") == 1.0


async def test_a_newly_stored_session_recomputes_the_factors(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any]
) -> None:
    """The captured session itself is no data point; the five stored ones give the median."""
    year = await _seed(hass, _sessions())
    entry, _manager = await _setup(hass, vehicles=(_glb(),))
    before = await _stored(hass, year)

    await _charge_once(hass, freezer)

    assert _state(hass, entry, "v001", "ac") == pytest.approx(1.12)
    (cached,) = hass_storage[STORE_KEY_EFFICIENCY]["data"]["factors"]
    assert cached["vehicle_id"] == "v001"
    assert cached["samples"] == 5
    after = await _stored(hass, year)
    assert after[: len(before)] == before


async def test_create_session_recomputes_the_factors(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    year = await _seed(hass, _sessions((1.1, 1.12, 1.2, 1.3)))
    entry, _manager = await _setup(hass, vehicles=(_glb(),))
    admin = MockUser(is_owner=True).add_to_hass(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CREATE_SESSION,
        {
            "location": "home",
            "vehicle_id": "v001",
            "plug_start": f"{year}-06-01T10:00:00+02:00",
            "plug_end": f"{year}-06-01T12:00:00+02:00",
            "soc_start": 20,
            "soc_end": 40,
            "energy_billed_kwh": 17.0,
        },
        blocking=True,
        context=Context(user_id=admin.id),
    )
    await hass.async_block_till_done()

    (cached,) = hass_storage[STORE_KEY_EFFICIENCY]["data"]["factors"]
    assert (cached["vehicle_id"], cached["charge_type"], cached["samples"]) == ("v001", "ac", 5)
    # The created session is the fifth data point, with a ratio of 1.0.
    assert _state(hass, entry, "v001", "ac") == pytest.approx(1.12)


async def test_delete_all_data_recomputes_to_the_default(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    await _seed(hass, _sessions())
    hass_storage[STORE_KEY_EFFICIENCY] = _cache(EfficiencyFactor("v001", "ac", 1.12, 5))
    entry, _manager = await _setup(hass, vehicles=(_glb(),))
    admin = MockUser(is_owner=True).add_to_hass(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_DELETE_ALL_DATA,
        {ATTR_CONFIRM: True},
        blocking=True,
        context=Context(user_id=admin.id),
    )
    await hass.async_block_till_done()

    assert _state(hass, entry, "v001", "ac") == 1.0
    assert hass_storage[STORE_KEY_EFFICIENCY]["data"]["factors"] == []


async def test_a_failing_recomputation_keeps_the_factors_and_the_session(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any]
) -> None:
    year = await _seed(hass, _sessions())
    hass_storage[STORE_KEY_EFFICIENCY] = _cache(EfficiencyFactor("v001", "ac", 1.05, 5))
    entry, _manager = await _setup(hass, vehicles=(_glb(),))

    with patch.object(EfficiencyStore, "async_save", side_effect=OSError("disk full")):
        await _charge_once(hass, freezer)

    assert _state(hass, entry, "v001", "ac") == pytest.approx(1.05)
    assert len(await _stored(hass, year)) == 6


async def test_the_entities_are_diagnostic_and_only_for_active_vehicles(
    hass: HomeAssistant,
) -> None:
    entry, _manager = await _setup(hass, vehicles=(_glb(), _eqb(active=False, cards=())))
    registry = er.async_get(hass)

    for charge_type in ("ac", "dc"):
        entity_id = _entity_id(hass, entry, "v001", charge_type)
        assert entity_id == f"sensor.glb_efficiency_{charge_type}"
        assert registry.async_get(entity_id).entity_category is EntityCategory.DIAGNOSTIC
        assert _entity_id(hass, entry, "v002", charge_type) is None


async def test_the_diagnostics_hold_the_factors_of_an_inactive_vehicle(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass_storage[STORE_KEY_EFFICIENCY] = _cache(EfficiencyFactor("v002", "ac", 1.077, 90))
    entry, _manager = await _setup(hass, vehicles=(_glb(), _eqb(active=False, cards=())))

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["efficiency"]["factors"] == [
        {"vehicle_id": "v002", "charge_type": "ac", "factor": 1.077, "samples": 90}
    ]


async def test_removing_the_integration_discards_the_factors(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any]
) -> None:
    await _seed(hass, _sessions())
    entry, _manager = await _setup(hass, vehicles=(_glb(),))
    await efficiency.async_recompute(hass)
    assert STORE_KEY_EFFICIENCY in hass_storage
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert STORE_KEY_EFFICIENCY not in hass_storage
