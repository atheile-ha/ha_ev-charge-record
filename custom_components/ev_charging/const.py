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

SOLAR_VALUATION_FEED_IN_TARIFF = "feed_in_tariff"
SOLAR_VALUATION_ZERO = "zero"
SOLAR_VALUATIONS = (
    SOLAR_VALUATION_FEED_IN_TARIFF,
    SOLAR_VALUATION_ZERO,
)

CARD_TYPE_RFID = "rfid"
CARD_TYPE_EMAID = "emaid"
CARD_TYPES = (CARD_TYPE_RFID, CARD_TYPE_EMAID)

# Normalized card uids that never count as an identification, regardless of
# how they were entered.
INVALID_CARD_UIDS = frozenset({"0", "UNKNOWN", "UNAVAILABLE"})

DEFAULT_POWER_THRESHOLD_KW = 0.5
DEFAULT_START_DEBOUNCE_S = 2
MIN_START_DEBOUNCE_S = 0
MAX_START_DEBOUNCE_S = 30
DEFAULT_IDENTIFICATION_WINDOW_S = 15
MIN_IDENTIFICATION_WINDOW_S = 0
MAX_IDENTIFICATION_WINDOW_S = 300

# Global hub settings (4.2). Only the fields without an entity selector are
# handled here; the remaining fields are added once entity roles exist.
DEFAULT_UPDATE_INTERVAL_S = 30
MIN_UPDATE_INTERVAL_S = 15
MAX_UPDATE_INTERVAL_S = 300
DEFAULT_GEOCODING_ENABLED = True
DEFAULT_GEOCODING_URL = "https://nominatim.openstreetmap.org/reverse"
DEFAULT_ESTIMATE_UNCERTAIN_THRESHOLD_PCT = 5

# Fixed, not user-configurable. Not part of the wallbox subentry schema.
MIN_PAUSE_MIN = 15
IDENTIFICATION_MAX_AGE_MIN = 5
FINAL_VALUES_GRACE_S = 2
ERROR_DEBOUNCE_S = 5
SESSION_TIMEOUT_H = 12
