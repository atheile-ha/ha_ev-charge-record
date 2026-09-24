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

# Direct read of the wallbox (expert options of the wallbox subentry).
DEFAULT_DIRECT_READ_PORT = 502
MIN_DIRECT_READ_PORT = 1
MAX_DIRECT_READ_PORT = 65535
DEFAULT_DIRECT_READ_UNIT_ID = 255
MIN_DIRECT_READ_UNIT_ID = 0
MAX_DIRECT_READ_UNIT_ID = 255

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

# A vehicle at home that reports charging counts as the car at the wallbox
# when the wallbox session began, or its charging power rose or fell, at most
# this many seconds ago, unless both powers are known and differ by more than
# the larger of the absolute and the relative tolerance.
SAME_VEHICLE_WINDOW_S = 120
SAME_VEHICLE_POWER_TOLERANCE_RATIO = 0.25
SAME_VEHICLE_POWER_TOLERANCE_MIN_KW = 1.5

# Geocoding (7.7). At most one request per this many seconds, serialized
# through one queue shared by every lookup.
GEOCODING_MIN_INTERVAL_S = 1.0
GEOCODING_TIMEOUT_S = 10

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

# What a mapping file's register entry may say. Anything else is rejected when
# the file is loaded.
MODBUS_FUNCTION_READ_HOLDING_REGISTERS = 3
MODBUS_MAX_REGISTER_ADDRESS = 65535
MODBUS_MAX_REGISTER_COUNT = 2
REGISTER_DECODE_UINT32_BIG_ENDIAN = "uint32_big_endian_word_order"
REGISTER_DECODES = (REGISTER_DECODE_UINT32_BIG_ENDIAN,)
REGISTER_FORMAT_HEX_UPPER_8 = "hex_upper_8"
REGISTER_FORMATS = (REGISTER_FORMAT_HEX_UPPER_8,)
# Roles a mapping file may feed from a register instead of an entity.
REGISTER_ROLES = ("identification",)

# Reading a role from the device happens in at most two sequences per session.
# The first starts this long after the session began, the second with the
# first charging phase. A sequence reads at the given interval, at most the
# given number of times, and stops with the first valid value.
DIRECT_READ_FIRST_DELAY_S = 10
DIRECT_READ_INTERVAL_S = 5
DIRECT_READ_MAX_READS = 10
# Bound for connecting and for the reply of one read.
DIRECT_READ_TIMEOUT_S = 3

# How a completed read of the identification failed.
READ_FAILURE_UNREACHABLE = "unreachable"
READ_FAILURE_INVALID_VALUE = "invalid_value"

# Where the reading of the identification stands, as shown on the live card.
READ_STATE_READING = "reading"
READ_STATE_WAITING = "waiting"
READ_STATE_READ = "read"
READ_STATE_UNREADABLE = "unreadable"

# What created the candidate of a session: the connector reporting a vehicle,
# or, without a connector report, the power passing the threshold.
CANDIDATE_TRIGGER_PLUG = "plug"
CANDIDATE_TRIGGER_POWER = "power"

# How the plug state of the wallbox is reported on the live card.
PLUG_REPORT_UNAVAILABLE = "unavailable"

# Why the live card has no expected charge end: the vehicle reports none while it does not charge.
CHARGE_END_MISSING_NO_POWER = "no_power"

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
SERVICE_RETRY_ADDRESS = "retry_address"
SERVICE_UPDATE_SESSION = "update_session"
SERVICE_DELETE_SESSION = "delete_session"
SERVICE_CREATE_SESSION = "create_session"
SERVICE_CLOSE_FOLLOWUP = "close_followup"
SERVICE_CORRECT_VEHICLE = "correct_vehicle"
ATTR_CONFIRM = "confirm"
ATTR_SESSION_ID = "id"
ATTR_VEHICLE_ID = "vehicle_id"

# Fields update_session may change (10, 13, 15). vehicle_id runs exclusively
# through correct_vehicle (7.8); location, plug_start, wallbox_id and every
# measured or derived energy field (I2) are never accepted here.
UPDATE_SESSION_FIELDS = (
    "soc_start",
    "soc_end",
    "odometer_km",
    "energy_billed_kwh",
    "cost",
    "charge_type",
    "address",
    "note",
    "provider",
    "plug_end",
)

# Live subscription block kinds (11.1, E37). The wallbox block is always
# first, the vehicle-driven blocks of running external sessions follow.
LIVE_BLOCK_WALLBOX = "wallbox"
LIVE_BLOCK_EXTERNAL = "external"

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
ISSUE_DIRECT_READ_UNREACHABLE = "direct_read_unreachable"
ISSUE_DIRECT_READ_INVALID_VALUE = "direct_read_invalid_value"
