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

COST_MODE_STATIC = "static"
COST_MODE_DYNAMIC = "dynamic"
COST_MODES = (COST_MODE_STATIC, COST_MODE_DYNAMIC)

# Only meaningful while cost_mode is dynamic; the static price then covers
# the whole charge instead.
SOLAR_VALUATION_FEED_IN_TARIFF = "feed_in_tariff"
SOLAR_VALUATION_ZERO = "zero"
SOLAR_VALUATIONS = (
    SOLAR_VALUATION_FEED_IN_TARIFF,
    SOLAR_VALUATION_ZERO,
)

DEFAULT_POWER_THRESHOLD_KW = 0.5
DEFAULT_START_DEBOUNCE_S = 20
MIN_START_DEBOUNCE_S = 5
MAX_START_DEBOUNCE_S = 120
DEFAULT_MIN_PAUSE_MIN = 15
DEFAULT_IDENTIFICATION_MAX_AGE_MIN = 5

# Fixed, not user-configurable. Not part of the wallbox subentry schema.
FINAL_VALUES_GRACE_S = 2
ERROR_DEBOUNCE_S = 5
SESSION_TIMEOUT_H = 12
