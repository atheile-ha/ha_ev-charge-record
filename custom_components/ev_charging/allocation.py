"""Grid and solar share, effective price and cost increments.

Pure functions and small value classes; nothing here touches Home Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass

from .const import SOLAR_VALUATION_ZERO


def grid_share(grid_power_kw: float, charge_power_kw: float) -> float | None:
    """Return the share of the charging power drawn from the grid, from 0 to 1.

    Grid import is charged to the vehicle in full, since without the charging
    session it would not have occurred; import above the charging power is
    capped and the rest belongs to the household. Feed-in means the charge is
    entirely solar. Returns None while there is no charging power to relate to.
    """
    if charge_power_kw <= 0:
        return None
    if grid_power_kw <= 0:
        return 0.0
    return min(grid_power_kw / charge_power_kw, 1.0)


def solar_share(share_grid: float) -> float:
    """Return the solar share belonging to a grid share."""
    return 1.0 - share_grid


def solar_price(valuation: str, price_feed_in: float | None) -> float | None:
    """Return the price at which the solar share is valued.

    None means the valuation asks for a feed-in price that is not available.
    """
    if valuation == SOLAR_VALUATION_ZERO:
        return 0.0
    return price_feed_in


def effective_price(
    share_grid: float, price_grid: float | None, price_solar: float | None
) -> float | None:
    """Return the price per kWh weighted by the grid and solar share.

    None if a price is missing for a share that is not zero.
    """
    share_solar = solar_share(share_grid)
    if share_grid > 0 and price_grid is None:
        return None
    if share_solar > 0 and price_solar is None:
        return None
    return (price_grid or 0.0) * share_grid + (price_solar or 0.0) * share_solar


@dataclass(frozen=True, slots=True)
class Allocation:
    """One counter increment split into grid and solar energy and its cost.

    cost is None when a needed price was not available for the increment.
    """

    grid_kwh: float
    solar_kwh: float
    cost: float | None


def allocate(
    delta_kwh: float, share_grid: float, price_grid: float | None, price_solar: float | None
) -> Allocation:
    """Split an energy increment and value it at the given prices."""
    grid = delta_kwh * share_grid
    solar = delta_kwh * solar_share(share_grid)
    price = effective_price(share_grid, price_grid, price_solar)
    return Allocation(
        grid_kwh=grid, solar_kwh=solar, cost=None if price is None else delta_kwh * price
    )


class MovingAverage:
    """Time-weighted average of a value that holds until it changes.

    Sensors report only on change, so a value stays in force until the next
    sample. The average over the window therefore weights each value by how
    long it was held.
    """

    def __init__(self, window_s: float) -> None:
        """Create an average over the last window_s seconds."""
        self._window_s = window_s
        self._samples: list[tuple[float, float]] = []

    def add(self, timestamp: float, value: float) -> None:
        """Record that the value became value at timestamp (seconds)."""
        self._samples.append((timestamp, value))
        self._trim(timestamp)

    def _trim(self, now: float) -> None:
        """Drop samples older than the window, keeping the one in force at its start."""
        start = now - self._window_s
        while len(self._samples) > 1 and self._samples[1][0] <= start:
            self._samples.pop(0)

    def average(self, now: float) -> float | None:
        """Return the average over the window ending at now, None without samples."""
        if not self._samples:
            return None
        self._trim(now)
        start = max(now - self._window_s, self._samples[0][0])
        if now <= start:
            return self._samples[-1][1]
        total = 0.0
        for index, (timestamp, value) in enumerate(self._samples):
            segment_start = max(timestamp, start)
            segment_end = self._samples[index + 1][0] if index + 1 < len(self._samples) else now
            segment_end = min(segment_end, now)
            if segment_end > segment_start:
                total += value * (segment_end - segment_start)
        return total / (now - start)

    def reset(self) -> None:
        """Forget all samples, for a source that became unavailable."""
        self._samples.clear()
