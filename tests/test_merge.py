"""Tests for merging stored sessions: the pure rules, without Home Assistant."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

import pytest
from custom_components.ev_charging.const import MAX_PHASES, MERGE_MARKER
from custom_components.ev_charging.models import (
    MergeRejectedError,
    Phase,
    Session,
    check_merge,
    merge_sessions,
)
from custom_components.ev_charging.store import MissingSessionsError, replace_by_merged

NOW = "2026-10-01T12:00:00+02:00"


def _year(session: Session) -> int:
    return datetime.fromisoformat(session.plug_start).year


def _session(session_id: str, start: str, end: str, **overrides: Any) -> Session:
    fields: dict[str, Any] = {
        "id": session_id,
        "location": "external",
        "plug_start": start,
        "plug_end": end,
        "identification_source": "vehicle_api",
        "vehicle_id": "v002",
        "vehicle_name": "Test car",
        "capacity_kwh": 80.0,
        "charge_type": "dc",
        "odometer_km": 7699.0,
        "address": "Synthetic street 1",
        "charge_duration_min": 20.0,
        "energy_raw_kwh": 10.0,
        "energy_estimated_kwh": 10.0,
        "energy_kwh": 10.0,
        "energy_grid_kwh": 0.0,
        "energy_solar_kwh": 0.0,
        "cost": 5.0,
        "phases": (Phase(start=start, end=end, duration_min=20.0),),
        "phase_count": 1,
    }
    fields.update(overrides)
    return Session(**fields)


def _three(third_odometer: float = 7700.0) -> list[Session]:
    return [
        _session(
            "b",
            "2026-09-05T18:40:00+02:00",
            "2026-09-05T19:00:00+02:00",
            soc_start=40,
            soc_end=55,
        ),
        _session(
            "a",
            "2026-09-05T18:00:00+02:00",
            "2026-09-05T18:20:00+02:00",
            soc_start=20,
            soc_end=38,
        ),
        _session(
            "c",
            "2026-09-05T19:30:00+02:00",
            "2026-09-05T19:50:00+02:00",
            odometer_km=third_odometer,
            soc_start=56,
            soc_end=80,
            energy_raw_kwh=12.5,
            energy_estimated_kwh=12.5,
            energy_kwh=12.5,
            cost=6.25,
        ),
    ]


def _merge(sessions: list[Session], odometer: dict[str, float] | None = None) -> Session:
    return merge_sessions(
        sessions,
        odometer or {},
        local_year=_year,
        estimate_uncertain_threshold_pct=5.0,
        modified_at=NOW,
    )


def test_three_sessions_merge_into_one_with_summed_values() -> None:
    """odometer 7699, 7699, 7700 merge; period, charge time, energy and cost add up."""
    sources = _three()

    merged = _merge(sources)

    assert merged.id == "a"
    assert merged.plug_start == "2026-09-05T18:00:00+02:00"
    assert merged.plug_end == "2026-09-05T19:50:00+02:00"
    assert merged.plug_duration_min == 110.0
    assert merged.charge_duration_min == 60.0
    assert merged.pause_duration_min == 50.0
    assert merged.energy_raw_kwh == 32.5
    assert merged.energy_estimated_kwh == 32.5
    assert merged.energy_kwh == 32.5
    assert merged.cost == 16.25
    assert merged.soc_start == 20
    assert merged.soc_end == 80
    assert merged.odometer_km == 7699.0
    assert merged.phase_count == 3
    assert [phase.start for phase in merged.phases] == sorted(
        phase.start for source in sources for phase in source.phases
    )
    assert merged.power_avg_kw == 32.5
    assert merged.modified_at == NOW
    assert MERGE_MARKER in merged.modified_fields


def test_merge_leaves_the_source_sessions_unchanged() -> None:
    """the stored values are only read and summed, never rewritten."""
    sources = _three()
    before = [replace(session) for session in sources]

    _merge(sources)

    assert sources == before


def test_more_than_one_km_apart_is_rejected() -> None:
    """7699, 7699 and 7701 are rejected."""
    with pytest.raises(MergeRejectedError) as raised:
        _merge(_three(third_odometer=7701.0))

    assert raised.value.check.violations == ("odometer_deviation",)


@pytest.mark.parametrize(
    ("field", "value", "violation"),
    [
        ("charge_type", "ac", "charge_type_differs"),
        ("card_uid", "SYNTHETIC01", "card_differs"),
        ("address", "Other street 2", "address_differs"),
        ("vehicle_id", "v001", "vehicle_differs"),
        ("location", "home_no_wallbox", "location_differs"),
    ],
)
def test_a_differing_condition_is_rejected(field: str, value: str, violation: str) -> None:
    """charge type, card, address, vehicle and location must match."""
    sources = _three()
    sources[2] = replace(sources[2], **{field: value})

    check = check_merge(sources, {}, _year)

    assert check.violations == (violation,)
    with pytest.raises(MergeRejectedError):
        _merge(sources)


def test_a_selection_across_the_turn_of_the_year_is_rejected() -> None:
    """sessions of two years are never merged."""
    sources = [
        _session("old", "2025-12-31T23:00:00+01:00", "2025-12-31T23:40:00+01:00"),
        _session("new", "2026-01-01T00:10:00+01:00", "2026-01-01T00:40:00+01:00"),
    ]

    assert check_merge(sources, {}, _year).violations == ("year_differs",)


def test_a_single_session_is_rejected() -> None:
    sources = _three()[:1]

    assert check_merge(sources, {}, _year).violations == ("too_few_sessions",)


def test_every_unmet_condition_is_reported() -> None:
    sources = _three(third_odometer=7705.0)
    sources[1] = replace(sources[1], card_uid="SYNTHETIC01", charge_type="ac")

    check = check_merge(sources, {}, _year)

    assert check.violations == ("odometer_deviation", "charge_type_differs", "card_differs")


def test_missing_card_and_address_in_every_session_count_as_equal() -> None:
    sources = [replace(session, card_uid=None, address=None) for session in _three()]

    assert check_merge(sources, {}, _year).ok


def test_unresolved_sessions_without_a_vehicle_count_as_equal() -> None:
    sources = [replace(session, vehicle_id=None) for session in _three()]

    assert _merge(sources).vehicle_id is None


def test_a_missing_odometer_needs_an_entered_value() -> None:
    """A session without odometer_km is only merged once a value is entered for it."""
    sources = _three(third_odometer=7699.0)
    sources[0] = replace(sources[0], odometer_km=None)

    check = check_merge(sources, {}, _year)
    assert check.violations == ("odometer_missing",)
    assert check.missing_odometer == ("b",)

    merged = _merge(sources, {"b": 7698.5})
    assert merged.odometer_km == 7698.5


def test_an_entered_odometer_counts_for_the_deviation_check() -> None:
    sources = _three()
    sources[0] = replace(sources[0], odometer_km=None)

    check = check_merge(sources, {"b": 7702.0}, _year)

    assert check.violations == ("odometer_deviation",)


def test_an_entered_odometer_is_ignored_for_a_session_that_has_one() -> None:
    merged = _merge(_three(), {"a": 1.0})

    assert merged.odometer_km == 7699.0


def test_a_sum_missing_in_one_session_is_null_and_open() -> None:
    """without energy_grid_kwh in one source, the merged value is null and open."""
    sources = _three()
    sources[1] = replace(sources[1], energy_grid_kwh=None)

    merged = _merge(sources)

    assert merged.energy_grid_kwh is None
    assert "energy_grid_kwh" in merged.open_fields
    assert merged.status == "followup_open"


def test_a_value_missing_in_every_session_stays_null_without_an_open_field() -> None:
    merged = _merge(_three())

    assert merged.energy_billed_kwh is None
    assert merged.energy_measured_kwh is None
    assert "energy_billed_kwh" not in merged.open_fields
    assert merged.open_fields == ()
    assert merged.status == "complete"


def test_a_missing_cost_in_one_session_is_null_and_open() -> None:
    sources = _three()
    sources[2] = replace(sources[2], cost=None)

    merged = _merge(sources)

    assert merged.cost is None
    assert "cost" in merged.open_fields


def test_source_open_fields_are_kept_only_while_still_missing() -> None:
    sources = _three()
    sources[1] = replace(sources[1], soc_end=None, open_fields=("soc_end", "cost"))

    merged = _merge(sources)

    assert merged.soc_end == 80
    assert merged.open_fields == ()


def test_soc_missing_everywhere_is_open() -> None:
    sources = [replace(session, soc_start=None, soc_end=None) for session in _three()]

    merged = _merge(sources)

    assert merged.soc_start is None
    assert merged.soc_end is None
    assert set(merged.open_fields) == {"soc_start", "soc_end"}


def test_the_worst_status_and_any_flag_carry_over() -> None:
    sources = _three()
    sources[2] = replace(sources[2], status="flagged", charge_error=True)
    sources[0] = replace(sources[0], location_conflict=True)

    merged = _merge(sources)

    assert merged.status == "flagged"
    assert merged.charge_error is True
    assert merged.location_conflict is True
    assert merged.identification_conflict is False


def test_notes_of_later_sessions_are_appended_in_order() -> None:
    sources = _three()
    sources[1] = replace(sources[1], note="first")
    sources[0] = replace(sources[0], note="second")
    sources[2] = replace(sources[2], note="first")

    assert _merge(sources).note == "first\nsecond"


def test_estimate_uncertain_follows_the_merged_state_of_charge() -> None:
    sources = [
        replace(session, estimate_uncertain=True, soc_start=50, soc_end=52)
        for session in _three()[:2]
    ]
    sources[1] = replace(sources[1], soc_start=52, soc_end=70)

    assert _merge(sources).estimate_uncertain is False


def test_too_many_phases_are_reduced_and_flag_the_session() -> None:
    start = datetime.fromisoformat("2026-09-05T00:00:00+02:00")

    def _phases(offset_min: int, count: int) -> tuple[Phase, ...]:
        return tuple(
            Phase(
                start=(start + timedelta(minutes=offset_min + 2 * i)).isoformat(),
                end=(start + timedelta(minutes=offset_min + 2 * i + 1)).isoformat(),
                duration_min=1.0,
            )
            for i in range(count)
        )

    first = replace(_three()[1], phases=_phases(0, 150), plug_start=start.isoformat())
    second = replace(
        _three()[0],
        phases=_phases(400, 150),
        plug_start=(start + timedelta(minutes=400)).isoformat(),
    )

    merged = _merge([first, second])

    assert len(merged.phases) == MAX_PHASES
    assert merged.phase_count == MAX_PHASES
    assert merged.status == "flagged"


# -------------------------------------------------------------- store step


def test_replace_by_merged_swaps_the_sources_for_the_merged_session() -> None:
    other = _session("x", "2026-08-01T10:00:00+02:00", "2026-08-01T11:00:00+02:00")
    current = [other, *_three()]

    result = replace_by_merged(current, ["a", "b", "c"], _merge)

    assert [session.id for session in result] == ["x", "a"]
    assert result[1].energy_kwh == 32.5


def test_replace_by_merged_raises_for_a_missing_source() -> None:
    with pytest.raises(MissingSessionsError):
        replace_by_merged(_three()[:2], ["a", "b", "c"], _merge)
