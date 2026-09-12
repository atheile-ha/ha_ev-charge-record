"""Constants for the ev_charging integration."""

DOMAIN = "ev_charging"

# Brand name, used as the config entry title. Brand names are not translated.
TITLE = "EV Charging"

STORE_KEY_RUNTIME = "ev_charging.runtime"
STORE_KEY_EFFICIENCY = "ev_charging.efficiency"


def store_key_sessions(year: int) -> str:
    """Return the store key holding the sessions of a given year."""
    return f"ev_charging.sessions_{year}"
