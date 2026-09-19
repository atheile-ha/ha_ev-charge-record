"""Tests for the grid and solar split, the effective price and the moving average."""

import pytest
from custom_components.ev_charging import allocation


def test_grid_share_of_partial_import() -> None:
    """11 kW charging with 3 kW import is 3 kW grid and 8 kW solar."""
    share = allocation.grid_share(3.0, 11.0)

    assert share == pytest.approx(3 / 11)
    assert allocation.solar_share(share) == pytest.approx(8 / 11)


def test_grid_share_is_capped_at_one() -> None:
    """Import above the charging power belongs to the household; the vehicle is all grid."""
    assert allocation.grid_share(15.0, 11.0) == 1.0


def test_feed_in_during_charging_is_all_solar() -> None:
    """Export while charging means the charge is solar only."""
    assert allocation.grid_share(-2.0, 11.0) == 0.0
    assert allocation.grid_share(0.0, 11.0) == 0.0


def test_grid_share_without_charging_power_is_undefined() -> None:
    """With no charging power there is nothing to relate the import to."""
    assert allocation.grid_share(3.0, 0.0) is None


def test_effective_price_weights_both_prices() -> None:
    """The effective price is the price of each share, weighted."""
    assert allocation.effective_price(0.25, 0.30, 0.08) == pytest.approx(0.25 * 0.30 + 0.75 * 0.08)


def test_effective_price_needs_the_price_of_every_present_share() -> None:
    """A missing price only matters for a share that is not zero."""
    assert allocation.effective_price(1.0, 0.30, None) == pytest.approx(0.30)
    assert allocation.effective_price(0.0, None, 0.08) == pytest.approx(0.08)
    assert allocation.effective_price(0.5, None, 0.08) is None
    assert allocation.effective_price(0.5, 0.30, None) is None


def test_solar_price_follows_the_valuation() -> None:
    """Free solar energy costs nothing whatever the feed-in price is."""
    assert allocation.solar_price("zero", 0.08) == 0.0
    assert allocation.solar_price("zero", None) == 0.0
    assert allocation.solar_price("feed_in_tariff", 0.08) == 0.08
    assert allocation.solar_price("feed_in_tariff", None) is None


def test_allocate_splits_energy_and_cost() -> None:
    """One increment is split by share and valued per share."""
    result = allocation.allocate(2.0, 0.25, 0.30, 0.08)

    assert result.grid_kwh == pytest.approx(0.5)
    assert result.solar_kwh == pytest.approx(1.5)
    assert result.cost == pytest.approx(0.5 * 0.30 + 1.5 * 0.08)


def test_allocate_without_price_has_no_cost() -> None:
    """An increment that cannot be valued carries no cost, but still its energy."""
    result = allocation.allocate(2.0, 0.5, None, 0.08)

    assert result.cost is None
    assert result.grid_kwh == pytest.approx(1.0)


def test_moving_average_weights_by_duration() -> None:
    """A value that held for longer counts for more."""
    average = allocation.MovingAverage(60)
    average.add(0, 0.0)
    average.add(40, 6.0)

    assert average.average(60) == pytest.approx(2.0)


def test_moving_average_forgets_old_samples() -> None:
    """Samples older than the window no longer count."""
    average = allocation.MovingAverage(60)
    average.add(0, 100.0)
    average.add(50, 2.0)

    assert average.average(130) == pytest.approx(2.0)


def test_moving_average_without_samples_is_undefined() -> None:
    """Nothing was measured yet."""
    average = allocation.MovingAverage(60)

    assert average.average(10) is None

    average.add(0, 1.0)
    average.reset()
    assert average.average(10) is None


def test_moving_average_of_a_single_fresh_sample() -> None:
    """At the moment of the sample the average is that sample."""
    average = allocation.MovingAverage(60)
    average.add(50, 4.0)

    assert average.average(50) == 4.0
