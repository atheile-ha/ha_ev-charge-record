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

# Wallbox plug state classes (5.1, 4.7). Whether the wallbox is plugged in
# and locked with the vehicle, as opposed to any other connector state.
PLUG_STATE_CONNECTED = "connected"
PLUG_STATE_NOT_CONNECTED = "not_connected"
PLUG_STATE_CLASSES = (PLUG_STATE_CONNECTED, PLUG_STATE_NOT_CONNECTED)

# error role classes, shared by the wallbox and vehicle error mapping (E29).
ERROR_CLASS_OK = "ok"
ERROR_CLASS_ERROR = "error"
ERROR_CLASSES = (ERROR_CLASS_OK, ERROR_CLASS_ERROR)

# Vehicle charge state classes (4.7). Never evaluated two-valued.
CHARGE_STATE_CHARGING = "charging"
CHARGE_STATE_CONNECTED_IDLE = "connected_idle"
CHARGE_STATE_DISCONNECTED = "disconnected"
CHARGE_STATE_ERROR = "error"
CHARGE_STATE_CLASSES = (
    CHARGE_STATE_CHARGING,
    CHARGE_STATE_CONNECTED_IDLE,
    CHARGE_STATE_DISCONNECTED,
    CHARGE_STATE_ERROR,
)
# An unmapped charge state value falls back to this class (I15).
CHARGE_STATE_DEFAULT = CHARGE_STATE_CONNECTED_IDLE

CHARGE_TYPES = CURRENT_TYPES

# Wallbox entity roles (5.1).
ROLE_CHARGE_POWER = "charge_power"
ROLE_ENERGY_TOTAL = "energy_total"
ROLE_ENERGY_SESSION = "energy_session"
ROLE_PLUG_STATE = "plug_state"
ROLE_IDENTIFICATION = "identification"
ROLE_ERROR = "error"

# Vehicle entity roles (5.2).
ROLE_SOC = "soc"
ROLE_SOC_TARGET = "soc_target"
ROLE_ODOMETER = "odometer"
ROLE_CHARGE_STATE = "charge_state"
ROLE_CHARGE_TYPE = "charge_type"
ROLE_LOCATION = "location"
ROLE_CHARGE_END = "charge_end"
ROLE_RANGE = "range"

# Hub entity roles (4.2).
ROLE_GRID_POWER = "grid_power"
ROLE_GRID_IMPORT = "grid_import"
ROLE_GRID_EXPORT = "grid_export"
ROLE_PRICE_GRID = "price_grid"
ROLE_PRICE_FEED_IN = "price_feed_in"

# Recognized units, normalized to the given canonical unit (5.3). No other
# unit is accepted; an unrecognized unit is treated as unresolvable rather
# than guessed at.
POWER_UNIT_FACTORS_TO_KW = {"kW": 1.0, "W": 0.001, "MW": 1000.0}
ENERGY_UNIT_FACTORS_TO_KWH = {"kWh": 1.0, "Wh": 0.001, "MWh": 1000.0}
DISTANCE_UNIT_FACTORS_TO_KM = {"km": 1.0, "m": 0.001, "mi": 1.609344}

RECORDER_STATE_LOOKBACK_DAYS = 90

# Sentinel selectable in a mapping step's class field, for a raw value that is
# not yet assigned a class. Rows left at this value are not stored; the
# value falls back to its runtime default until it is mapped explicitly.
# Used as a selector translation key, so it must match [a-z0-9-_]+ without a
# leading or trailing hyphen or underscore.
MAPPING_UNMAPPED = "unmapped"

# Repair issue translation keys (12.3).
ISSUE_ROLE_ENTITY_REMOVED = "role_entity_removed"
ISSUE_ROLE_UNIT_CHANGED = "role_unit_changed"
