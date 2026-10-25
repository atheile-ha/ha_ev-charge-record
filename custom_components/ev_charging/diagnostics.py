"""Diagnostics download: settings, subentries, runtime state, efficiency factors, journal."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.diagnostics.util import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import efficiency, journal
from .store import RuntimeStore

# Personal fields. In the subentry of a vehicle a card holds its id and its
# label under uid and label.
TO_REDACT = frozenset(
    {"vin", "card_uid", "card_label", "address", "latitude", "longitude", "uid", "label"}
)
# Card ids in the journal are already shortened to their last characters and stay visible.
JOURNAL_TO_REDACT = TO_REDACT - {"card_uid"}


def _entry_moment(entry: dict[str, Any]) -> datetime:
    """Return the moment of a journal entry for sorting; an unreadable one sorts first."""
    value = entry.get("time")
    moment = dt_util.parse_datetime(value) if isinstance(value, str) else None
    return moment or datetime.min.replace(tzinfo=dt_util.UTC)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return the diagnostics of the hub entry, the personal fields redacted."""
    runtime = await RuntimeStore(hass).async_load()
    entries = sorted(journal.entries(hass), key=_entry_moment)
    return {
        **async_redact_data(
            {
                "hub": dict(entry.data),
                "subentries": [
                    {
                        "subentry_id": subentry.subentry_id,
                        "subentry_type": subentry.subentry_type,
                        "title": subentry.title,
                        "data": dict(subentry.data),
                    }
                    for subentry in entry.subentries.values()
                ],
                "runtime": runtime,
                # Factors of every vehicle with data, active or not.
                "efficiency": efficiency.as_dict(hass),
            },
            TO_REDACT,
        ),
        "journal": async_redact_data(entries, JOURNAL_TO_REDACT),
    }
