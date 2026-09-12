"""Constants for the ev_charging integration."""

DOMAIN = "ev_charging"

# Brand name, used as the config entry title. Brand names are not translated.
TITLE = "EV Charging"

STORE_KEY_RUNTIME = "ev_charging.runtime"
STORE_KEY_EFFICIENCY = "ev_charging.efficiency"


def store_key_sessions(year: int) -> str:
    """Return the store key holding the sessions of a given year."""
    return f"ev_charging.sessions_{year}"


# Hub config entry data keys. These hold the highest sequence number ever
# assigned to a subentry of that type, so an id is never handed out twice,
# even after the subentry that held it was removed.
CONF_WALLBOX_SEQUENCE = "wallbox_seq"
CONF_VEHICLE_SEQUENCE = "vehicle_seq"

SUBENTRY_TYPE_WALLBOX = "wallbox"
SUBENTRY_TYPE_VEHICLE = "vehicle"

WALLBOX_ID_PREFIX = "wb"
VEHICLE_ID_PREFIX = "v"

CURRENT_TYPE_AC = "ac"
CURRENT_TYPE_DC = "dc"
CURRENT_TYPES = (CURRENT_TYPE_AC, CURRENT_TYPE_DC)

SESSION_STRATEGY_PLUG_STATE = "plug_state"
SESSION_STRATEGY_POWER_PAUSE = "power_pause"
SESSION_STRATEGIES = (SESSION_STRATEGY_PLUG_STATE, SESSION_STRATEGY_POWER_PAUSE)

SOLAR_VALUATION_FEED_IN_TARIFF = "feed_in_tariff"
SOLAR_VALUATION_ZERO = "zero"
SOLAR_VALUATION_FIXED = "fixed"
SOLAR_VALUATIONS = (
    SOLAR_VALUATION_FEED_IN_TARIFF,
    SOLAR_VALUATION_ZERO,
    SOLAR_VALUATION_FIXED,
)

DEFAULT_POWER_THRESHOLD_KW = 0.5
DEFAULT_START_DEBOUNCE_S = 20
MIN_START_DEBOUNCE_S = 5
MAX_START_DEBOUNCE_S = 120
DEFAULT_MIN_PAUSE_MIN = 15
DEFAULT_SESSION_END_PAUSE_MIN = 240
DEFAULT_FINAL_VALUES_GRACE_MIN = 30
DEFAULT_IDENTIFICATION_MAX_AGE_MIN = 5
DEFAULT_ERROR_DEBOUNCE_S = 30
DEFAULT_SESSION_STALE_H = 12
