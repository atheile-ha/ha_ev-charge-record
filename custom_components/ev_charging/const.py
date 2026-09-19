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
COST_MODES = (COST_MODE_DYNAMIC, COST_MODE_STATIC)

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

# Runtime behavior of the session capture.
POWER_TOLERANCE_FACTOR = 1.15
# A counter step is judged against at least this much elapsed time, so the
# quantization of a coarse counter cannot make a single tick look impossible.
MIN_PLAUSIBILITY_INTERVAL_S = 60
GRID_POWER_WINDOW_S = 60
MAX_PHASES = 200
PERSIST_INTERVAL_S = 120
COUNTER_CHECK_INTERVAL_S = 60
LIVE_PUSH_INTERVAL_S = 1
# Relative deviation between the two energy counters above which a session is flagged.
COUNTER_DEVIATION_TOLERANCE = 0.05
# The mean charging power above which a session without a reported charge type
# is treated as DC.
DC_POWER_THRESHOLD_KW = 25

# Wallbox session states. Published as the state of the wallbox state
# sensor; completed is transient and never a resting state.
SESSION_STATE_IDLE = "idle"
SESSION_STATE_CANDIDATE = "candidate"
SESSION_STATE_CHARGING = "charging"
SESSION_STATE_PAUSED = "paused"
SESSION_STATE_ERROR = "error"
SESSION_STATE_AWAITING_FINAL = "awaiting_final"
SESSION_STATES = (
    SESSION_STATE_IDLE,
    SESSION_STATE_CANDIDATE,
    SESSION_STATE_CHARGING,
    SESSION_STATE_PAUSED,
    SESSION_STATE_ERROR,
    SESSION_STATE_AWAITING_FINAL,
)

# Values of the active vehicle sensor when no vehicle name applies.
ACTIVE_VEHICLE_NONE = "none"
ACTIVE_VEHICLE_GUEST = "guest"
ACTIVE_VEHICLE_UNRESOLVED = "unresolved"

# Energy counter selection.
COUNTER_TOTAL = "total"
COUNTER_SESSION = "session"

# Location values reported by a device tracker.
TRACKER_STATE_HOME = "home"
TRACKER_STATE_NOT_HOME = "not_home"

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

CHARGE_TYPE_UNKNOWN = "unknown"
CHARGE_TYPES = (*CURRENT_TYPES, CHARGE_TYPE_UNKNOWN)

CHARGE_TYPE_SOURCE_ENTITY = "entity"
CHARGE_TYPE_SOURCE_WALLBOX_CONFIG = "wallbox_config"
CHARGE_TYPE_SOURCE_HEURISTIC = "heuristic"
CHARGE_TYPE_SOURCES = (
    CHARGE_TYPE_SOURCE_ENTITY,
    CHARGE_TYPE_SOURCE_WALLBOX_CONFIG,
    CHARGE_TYPE_SOURCE_HEURISTIC,
)

# Session identification sources (6.2, 7.8).
IDENTIFICATION_SOURCE_RFID = "rfid"
IDENTIFICATION_SOURCE_EMAID = "emaid"
IDENTIFICATION_SOURCE_VEHICLE_API = "vehicle_api"
IDENTIFICATION_SOURCE_MANUAL = "manual"
IDENTIFICATION_SOURCE_UNRESOLVED = "unresolved"
IDENTIFICATION_SOURCES = (
    IDENTIFICATION_SOURCE_RFID,
    IDENTIFICATION_SOURCE_EMAID,
    IDENTIFICATION_SOURCE_VEHICLE_API,
    IDENTIFICATION_SOURCE_MANUAL,
    IDENTIFICATION_SOURCE_UNRESOLVED,
)

# Session location (6.2, 7.4).
LOCATION_HOME = "home"
LOCATION_HOME_NO_WALLBOX = "home_no_wallbox"
LOCATION_EXTERNAL = "external"
LOCATIONS = (LOCATION_HOME, LOCATION_HOME_NO_WALLBOX, LOCATION_EXTERNAL)

# Session status (6.2).
SESSION_STATUS_COMPLETE = "complete"
SESSION_STATUS_FOLLOWUP_OPEN = "followup_open"
SESSION_STATUS_FLAGGED = "flagged"
SESSION_STATUSES = (SESSION_STATUS_COMPLETE, SESSION_STATUS_FOLLOWUP_OPEN, SESSION_STATUS_FLAGGED)

# Session store schema (6.1). Present from the first version so a future
# schema change has an async_migrate_func to extend rather than add.
STORAGE_VERSION_SESSIONS = 1
STORAGE_MINOR_VERSION_SESSIONS = 1
STORAGE_VERSION_RUNTIME = 1
STORAGE_MINOR_VERSION_RUNTIME = 1

# A raw value with no meaning for a given role (E31, 4.7). Leaves the last
# valid class of that role unchanged; distinct from a value missing from the
# mapping entirely, which is unresolved and repair-worthy.
MAPPING_CLASS_NEUTRAL = "neutral"

# Only this mapping file format is understood (4.7).
MAPPING_FORMAT_VERSION = 1

# Selectable in the vehicle device-choice step in place of a mapping id, for a
# vehicle with no connected online integration (5.2). Never stored: resolves
# to mapping_id = None.
NO_VEHICLE_INTEGRATION = "none"

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

SERVICE_DELETE_ALL_DATA = "delete_all_data"
ATTR_CONFIRM = "confirm"

# Frontend. The bundle holds the panel and all dashboard cards; it is served
# from a path of its own so it never collides with the panel's route.
PANEL_URL_PATH = "ev_charging"
PANEL_WEBCOMPONENT = "ev-charging-panel"
PANEL_ICON = "mdi:ev-station"
FRONTEND_BUNDLE_FILENAME = "ev-charging.js"
FRONTEND_STATIC_URL_PATH = "/ev_charging_static/ev-charging.js"

# sessions/list without a year returns this many of the newest sessions.
DEFAULT_RECENT_LIMIT = 10
MAX_LIST_LIMIT = 500

# WebSocket command for the live card.
WS_LIVE_SUBSCRIBE = "ev_charging/live/subscribe"

# Repair issue translation keys (12.3).
ISSUE_ROLE_ENTITY_REMOVED = "role_entity_removed"
ISSUE_ROLE_UNIT_CHANGED = "role_unit_changed"
ISSUE_UNKNOWN_MAPPING_VALUE = "unknown_mapping_value"
ISSUE_MAPPING_SOURCE_BELOW_MIN_VERSION = "mapping_source_below_min_version"
ISSUE_UNKNOWN_CARD = "unknown_card"
ISSUE_COUNTER_SWITCHED = "energy_counter_switched"
