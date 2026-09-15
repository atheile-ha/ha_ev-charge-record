"""Config flow for the ev_charging integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentry,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.data_entry_flow import SectionConfig, section
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    ObjectSelector,
    ObjectSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from . import resolver
from .const import (
    CARD_TYPE_EMAID,
    CARD_TYPE_RFID,
    CHARGE_STATE_CLASSES,
    CHARGE_TYPES,
    CONF_VEHICLE_SEQUENCE,
    CONF_WALLBOX_SEQUENCE,
    COST_MODE_DYNAMIC,
    COST_MODES,
    CURRENT_TYPE_AC,
    CURRENT_TYPES,
    DEFAULT_IDENTIFICATION_WINDOW_S,
    DEFAULT_POWER_THRESHOLD_KW,
    DEFAULT_START_DEBOUNCE_S,
    DOMAIN,
    ERROR_CLASSES,
    INVALID_CARD_UIDS,
    MAPPING_UNMAPPED,
    MAX_IDENTIFICATION_WINDOW_S,
    MAX_START_DEBOUNCE_S,
    MAX_UPDATE_INTERVAL_S,
    MIN_IDENTIFICATION_WINDOW_S,
    MIN_START_DEBOUNCE_S,
    MIN_UPDATE_INTERVAL_S,
    PLUG_STATE_CLASSES,
    SOLAR_VALUATIONS,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
    VEHICLE_ID_PREFIX,
    WALLBOX_ID_PREFIX,
)
from .models import Card, EntityRole, HubSettings, Vehicle, Wallbox, normalize_card_uid

PRESETS_DIR = Path(__file__).parent / "presets"

# Shown in the vehicle dialog's identification hint when no value can be read.
NO_IDENTIFICATION_HINT = "-"


def _entity_id(role: EntityRole | None) -> str | None:
    """Return a role's stored entity_id, for use as a form default."""
    return role.entity_id if role is not None else None


def _is_binary_sensor(entity_id: str) -> bool:
    """Return whether entity_id belongs to the binary_sensor domain."""
    return entity_id.startswith("binary_sensor.")


async def _async_mapping_step(
    flow: ConfigSubentryFlow,
    *,
    step_id: str,
    user_input: dict[str, Any] | None,
    entity_id: str,
    preset_role_key: str,
    classes: tuple[str, ...],
    class_translation_key: str,
    existing: dict[str, str],
) -> tuple[dict[str, str] | None, SubentryFlowResult | None]:
    """Handle one step of a state mapping (4.7): preset, recorder, free entry.

    Returns (mapping, None) once the user has submitted rows, or once a
    bundled preset already covers every candidate value with nothing left to
    classify. Returns (None, form_result) to show the step's form only when
    something remains for the user to decide.
    """
    if user_input is not None:
        return resolver.mapping_from_rows(user_input["mapping"]), None

    hass = flow.hass
    role = resolver.build_role(hass, entity_id)
    platform = resolver.resolve_platform(hass, role)
    preset = await hass.async_add_executor_job(resolver.find_preset, PRESETS_DIR, platform)
    preset_data = (preset or {}).get(preset_role_key)
    preset_values = preset_data.get("values") if preset_data else None
    reference = resolver.format_preset_reference(preset_data) if preset_data else ""

    discovered = await resolver.async_query_recorder_states(hass, entity_id)
    rows = resolver.build_mapping_rows(
        existing=existing, preset_values=preset_values, discovered=discovered
    )

    if preset_values and all(row["class"] != MAPPING_UNMAPPED for row in rows):
        return resolver.mapping_from_rows(rows), None

    schema = vol.Schema(
        {
            vol.Required("mapping", default=rows): ObjectSelector(
                ObjectSelectorConfig(
                    multiple=True,
                    label_field="raw_value",
                    translation_key="state_mapping",
                    fields={
                        "raw_value": {"selector": TextSelector(), "required": True},
                        "class": {
                            "selector": SelectSelector(
                                SelectSelectorConfig(
                                    options=[*classes, MAPPING_UNMAPPED],
                                    translation_key=class_translation_key,
                                )
                            ),
                            "required": True,
                        },
                    },
                )
            ),
        }
    )
    form = flow.async_show_form(
        step_id=step_id,
        data_schema=schema,
        description_placeholders={"reference": reference},
    )
    return None, form


class EvChargingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ev_charging."""

    VERSION = 3
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm the setup. Global settings start at their defaults."""
        if user_input is None:
            return self.async_show_form(step_id="user")

        data = {
            CONF_WALLBOX_SEQUENCE: 0,
            CONF_VEHICLE_SEQUENCE: 0,
            **HubSettings().to_dict(),
        }
        return self.async_create_entry(title=TITLE, data=data)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit the global settings of the hub entry."""
        entry = self._get_reconfigure_entry()
        defaults = HubSettings.from_dict(entry.data)
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = self._validate_settings(user_input)
            if not errors:
                settings = HubSettings(
                    update_interval_s=user_input["update_interval_s"],
                    solar_valuation=user_input["solar_valuation"],
                    geocoding_enabled=user_input["geocoding_enabled"],
                    geocoding_url=user_input["geocoding_url"],
                    geocoding_contact=user_input.get("geocoding_contact") or None,
                    estimate_uncertain_threshold_pct=user_input["estimate_uncertain_threshold_pct"],
                    grid_power=resolver.build_role(self.hass, user_input.get("grid_power") or None),
                    grid_power_inverted=user_input["grid_power_inverted"],
                    grid_import=resolver.build_role(
                        self.hass, user_input.get("grid_import") or None
                    ),
                    grid_export=resolver.build_role(
                        self.hass, user_input.get("grid_export") or None
                    ),
                    price_grid=resolver.build_role(self.hass, user_input.get("price_grid") or None),
                    price_grid_fixed=user_input.get("price_grid_fixed"),
                    price_feed_in=resolver.build_role(
                        self.hass, user_input.get("price_feed_in") or None
                    ),
                    price_feed_in_fixed=user_input.get("price_feed_in_fixed"),
                )
                return self.async_update_reload_and_abort(
                    entry, data={**entry.data, **settings.to_dict()}
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._settings_schema(defaults=defaults),
            errors=errors,
        )

    def _validate_settings(self, user_input: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}
        if not (MIN_UPDATE_INTERVAL_S <= user_input["update_interval_s"] <= MAX_UPDATE_INTERVAL_S):
            errors["update_interval_s"] = "update_interval_out_of_range"
        if user_input["geocoding_enabled"] and not user_input.get("geocoding_contact"):
            errors["geocoding_contact"] = "geocoding_contact_required"
        if not (0 < user_input["estimate_uncertain_threshold_pct"] <= 100):
            errors["estimate_uncertain_threshold_pct"] = "estimate_uncertain_threshold_out_of_range"
        if user_input.get("grid_power") and (
            user_input.get("grid_import") or user_input.get("grid_export")
        ):
            errors["grid_power"] = "grid_source_conflict"
        if user_input.get("price_grid") and user_input.get("price_grid_fixed") is not None:
            errors["price_grid"] = "price_source_conflict"
        if user_input.get("price_feed_in") and user_input.get("price_feed_in_fixed") is not None:
            errors["price_feed_in"] = "price_source_conflict"
        return errors

    def _settings_schema(self, *, defaults: HubSettings) -> vol.Schema:
        d = defaults
        return vol.Schema(
            {
                vol.Required("update_interval_s", default=d.update_interval_s): vol.Coerce(int),
                vol.Required("solar_valuation", default=d.solar_valuation): SelectSelector(
                    SelectSelectorConfig(
                        options=list(SOLAR_VALUATIONS), translation_key="solar_valuation"
                    )
                ),
                vol.Required("geocoding_enabled", default=d.geocoding_enabled): bool,
                vol.Required("geocoding_url", default=d.geocoding_url): str,
                vol.Optional(
                    "geocoding_contact",
                    description={"suggested_value": d.geocoding_contact},
                ): str,
                vol.Required(
                    "estimate_uncertain_threshold_pct",
                    default=d.estimate_uncertain_threshold_pct,
                ): vol.Coerce(float),
                vol.Optional("grid_power", default=_entity_id(d.grid_power)): vol.Any(
                    None, EntitySelector()
                ),
                vol.Required("grid_power_inverted", default=d.grid_power_inverted): bool,
                vol.Optional("grid_import", default=_entity_id(d.grid_import)): vol.Any(
                    None, EntitySelector()
                ),
                vol.Optional("grid_export", default=_entity_id(d.grid_export)): vol.Any(
                    None, EntitySelector()
                ),
                vol.Optional("price_grid", default=_entity_id(d.price_grid)): vol.Any(
                    None, EntitySelector()
                ),
                vol.Optional("price_grid_fixed", default=d.price_grid_fixed): vol.Any(
                    None, vol.Coerce(float)
                ),
                vol.Optional("price_feed_in", default=_entity_id(d.price_feed_in)): vol.Any(
                    None, EntitySelector()
                ),
                vol.Optional("price_feed_in_fixed", default=d.price_feed_in_fixed): vol.Any(
                    None, vol.Coerce(float)
                ),
            }
        )

    @classmethod
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this handler."""
        return {
            SUBENTRY_TYPE_WALLBOX: WallboxSubentryFlow,
            SUBENTRY_TYPE_VEHICLE: VehicleSubentryFlow,
        }


def _allocate_id(entry: ConfigEntry, hass: Any, *, sequence_key: str, prefix: str) -> str:
    """Return the next id for a sequence, persisting the new high-water mark.

    The sequence is stored on the hub entry so that a removed subentry never
    hands its id to a later one.
    """
    next_seq = entry.data.get(sequence_key, 0) + 1
    hass.config_entries.async_update_entry(entry, data={**entry.data, sequence_key: next_seq})
    return f"{prefix}{next_seq:03d}"


class WallboxSubentryFlow(ConfigSubentryFlow):
    """Handle creating and editing the wallbox subentry."""

    def __init__(self) -> None:
        """Initialize flow state carried between steps."""
        self._subentry: ConfigSubentry | None = None
        self._pending: dict[str, Any] = {}

    @property
    def _entry(self) -> ConfigEntry:
        return self.hass.config_entries.async_get_known_entry(self.handler[0])

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Create the wallbox subentry. Only one instance is allowed."""
        if self._entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX):
            return self.async_abort(reason="single_wallbox_allowed")
        return await self._async_step(user_input, subentry=None)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Edit the existing wallbox subentry."""
        return await self._async_step(user_input, subentry=self._get_reconfigure_subentry())

    async def _async_step(
        self, user_input: dict[str, Any] | None, *, subentry: ConfigSubentry | None
    ) -> SubentryFlowResult:
        step_id = "reconfigure" if subentry else "user"
        defaults = Wallbox.from_dict(subentry.data) if subentry else None
        self._subentry = subentry
        errors: dict[str, str] = {}

        if user_input is not None:
            roles = user_input.pop("roles")
            user_input.update(roles)
            expert = user_input.pop("expert")
            user_input.update(expert)
            user_input["manufacturer"] = user_input.get("manufacturer") or None
            user_input["model"] = user_input.get("model") or None
            errors = self._validate(user_input)
            if not errors:
                self._pending = user_input
                return await self.async_step_plug_state_mapping()

        return self.async_show_form(
            step_id=step_id, data_schema=self._schema(defaults=defaults), errors=errors
        )

    def _validate(self, user_input: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}
        if not (MIN_START_DEBOUNCE_S <= user_input["start_debounce_s"] <= MAX_START_DEBOUNCE_S):
            errors["start_debounce_s"] = "start_debounce_out_of_range"
        if not (
            MIN_IDENTIFICATION_WINDOW_S
            <= user_input["identification_window_s"]
            <= MAX_IDENTIFICATION_WINDOW_S
        ):
            errors["identification_window_s"] = "identification_window_out_of_range"
        if user_input["max_power_kw"] <= 0:
            errors["max_power_kw"] = "must_be_positive"
        if user_input.get("power_threshold_kw", 0) < 0:
            errors["power_threshold_kw"] = "must_not_be_negative"
        if not user_input.get("charge_power"):
            errors["charge_power"] = "charge_power_required"
        if not user_input.get("plug_state"):
            errors["plug_state"] = "plug_state_required"
        if not user_input.get("energy_total") and not user_input.get("energy_session"):
            errors["energy_total"] = "energy_counter_required"
        return errors

    async def async_step_plug_state_mapping(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Map the wallbox's raw plug state values onto connected/not_connected (4.7)."""
        existing = self._subentry_wallbox().plug_state_mapping if self._subentry else {}
        mapping, form = await _async_mapping_step(
            self,
            step_id="plug_state_mapping",
            user_input=user_input,
            entity_id=self._pending["plug_state"],
            preset_role_key="plug_state",
            classes=PLUG_STATE_CLASSES,
            class_translation_key="plug_state_class",
            existing=existing,
        )
        if form is not None:
            return form
        self._pending["plug_state_mapping"] = mapping

        error_entity = self._pending.get("error")
        if error_entity and not _is_binary_sensor(error_entity):
            return await self.async_step_error_mapping()
        self._pending["error_mapping"] = {}
        return self._finish()

    async def async_step_error_mapping(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Map the wallbox error entity's raw state values onto ok/error (E29, 4.7)."""
        existing = self._subentry_wallbox().error_mapping if self._subentry else {}
        mapping, form = await _async_mapping_step(
            self,
            step_id="error_mapping",
            user_input=user_input,
            entity_id=self._pending["error"],
            preset_role_key="error",
            classes=ERROR_CLASSES,
            class_translation_key="error_class",
            existing=existing,
        )
        if form is not None:
            return form
        self._pending["error_mapping"] = mapping
        return self._finish()

    def _subentry_wallbox(self) -> Wallbox:
        assert self._subentry is not None
        return Wallbox.from_dict(self._subentry.data)

    def _finish(self) -> SubentryFlowResult:
        data = self._pending
        wallbox_kwargs = dict(
            name=data["name"],
            manufacturer=data["manufacturer"],
            model=data["model"],
            current_type=data["current_type"],
            max_power_kw=data["max_power_kw"],
            power_threshold_kw=data["power_threshold_kw"],
            start_debounce_s=data["start_debounce_s"],
            identification_window_s=data["identification_window_s"],
            charge_power=resolver.build_role(self.hass, data.get("charge_power")),
            energy_total=resolver.build_role(self.hass, data.get("energy_total")),
            energy_session=resolver.build_role(self.hass, data.get("energy_session")),
            plug_state=resolver.build_role(self.hass, data.get("plug_state")),
            plug_state_mapping=data["plug_state_mapping"],
            identification=resolver.build_role(self.hass, data.get("identification")),
            error=resolver.build_role(self.hass, data.get("error")),
            error_mapping=data["error_mapping"],
        )

        if self._subentry:
            wallbox = Wallbox(id=self._subentry_wallbox().id, **wallbox_kwargs)
            return self.async_update_reload_and_abort(
                self._entry, self._subentry, title=wallbox.name, data=wallbox.to_dict()
            )

        wallbox_id = _allocate_id(
            self._entry, self.hass, sequence_key=CONF_WALLBOX_SEQUENCE, prefix=WALLBOX_ID_PREFIX
        )
        wallbox = Wallbox(id=wallbox_id, **wallbox_kwargs)
        result = self.async_create_entry(title=wallbox.name, data=wallbox.to_dict())
        self.hass.config_entries.async_schedule_reload(self._entry.entry_id)
        return result

    def _schema(self, *, defaults: Wallbox | None) -> vol.Schema:
        d = defaults
        return vol.Schema(
            {
                vol.Required("name", default=d.name if d else vol.UNDEFINED): str,
                vol.Optional(
                    "manufacturer",
                    description={"suggested_value": d.manufacturer if d else None},
                ): str,
                vol.Optional("model", description={"suggested_value": d.model if d else None}): str,
                vol.Required(
                    "current_type", default=d.current_type if d else CURRENT_TYPE_AC
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(CURRENT_TYPES), translation_key="current_type"
                    )
                ),
                vol.Required(
                    "max_power_kw", default=d.max_power_kw if d else vol.UNDEFINED
                ): vol.Coerce(float),
                vol.Required("roles"): section(
                    vol.Schema(
                        {
                            vol.Optional(
                                "charge_power", default=_entity_id(d.charge_power) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "energy_total", default=_entity_id(d.energy_total) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "energy_session",
                                default=_entity_id(d.energy_session) if d else None,
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "plug_state", default=_entity_id(d.plug_state) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "identification",
                                default=_entity_id(d.identification) if d else None,
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "error", default=_entity_id(d.error) if d else None
                            ): vol.Any(None, EntitySelector()),
                        }
                    ),
                    SectionConfig(collapsed=False),
                ),
                vol.Required("expert"): section(
                    vol.Schema(
                        {
                            vol.Required(
                                "power_threshold_kw",
                                default=(d.power_threshold_kw if d else DEFAULT_POWER_THRESHOLD_KW),
                            ): vol.Coerce(float),
                            vol.Required(
                                "start_debounce_s",
                                default=(d.start_debounce_s if d else DEFAULT_START_DEBOUNCE_S),
                            ): vol.Coerce(int),
                            vol.Required(
                                "identification_window_s",
                                default=(
                                    d.identification_window_s
                                    if d
                                    else DEFAULT_IDENTIFICATION_WINDOW_S
                                ),
                            ): vol.Coerce(int),
                        }
                    ),
                    SectionConfig(collapsed=True),
                ),
            }
        )


class VehicleSubentryFlow(ConfigSubentryFlow):
    """Handle creating and editing a vehicle subentry, including its cards."""

    def __init__(self) -> None:
        """Initialize flow state carried between steps."""
        self._subentry: ConfigSubentry | None = None
        self._pending: dict[str, Any] = {}

    @property
    def _entry(self) -> ConfigEntry:
        return self.hass.config_entries.async_get_known_entry(self.handler[0])

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Create a new vehicle subentry."""
        return await self._async_step(user_input, subentry=None)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Edit an existing vehicle subentry."""
        return await self._async_step(user_input, subentry=self._get_reconfigure_subentry())

    async def _async_step(
        self, user_input: dict[str, Any] | None, *, subentry: ConfigSubentry | None
    ) -> SubentryFlowResult:
        step_id = "reconfigure" if subentry else "user"
        defaults = Vehicle.from_dict(subentry.data) if subentry else None
        self._subentry = subentry
        errors: dict[str, str] = {}

        if user_input is not None:
            roles = user_input.pop("roles")
            user_input.update(roles)
            user_input["vin"] = user_input.get("vin") or None
            user_input["manufacturer"] = user_input.get("manufacturer") or None
            user_input["model"] = user_input.get("model") or None
            own_subentry_id = subentry.subentry_id if subentry else None
            cards, errors = self._validate(user_input, own_subentry_id=own_subentry_id)
            if not errors:
                self._pending = user_input
                self._pending["cards"] = cards
                return await self.async_step_charge_state_mapping()

        return self.async_show_form(
            step_id=step_id,
            data_schema=self._schema(defaults=defaults),
            errors=errors,
            description_placeholders={"identification_hint": self._identification_hint()},
        )

    def _identification_hint(self) -> str:
        """Return the wallbox's currently reported identification value, if any."""
        wallboxes = self._entry.get_subentries_of_type(SUBENTRY_TYPE_WALLBOX)
        if not wallboxes:
            return NO_IDENTIFICATION_HINT
        wallbox = Wallbox.from_dict(next(iter(wallboxes)).data)
        entity_id = resolver.resolve_entity_id(self.hass, wallbox.identification)
        if entity_id is None:
            return NO_IDENTIFICATION_HINT
        state = self.hass.states.get(entity_id)
        if state is None:
            return NO_IDENTIFICATION_HINT
        normalized = normalize_card_uid(state.state)
        if not normalized or normalized in INVALID_CARD_UIDS:
            return NO_IDENTIFICATION_HINT
        return normalized

    def _validate(
        self, user_input: dict[str, Any], *, own_subentry_id: str | None
    ) -> tuple[tuple[Card, ...], dict[str, str]]:
        errors: dict[str, str] = {}
        if not user_input.get("is_guest") and user_input.get("capacity_kwh") is None:
            errors["capacity_kwh"] = "capacity_required"

        if user_input.get("identify_by_vehicle_api") and (
            not user_input.get("charge_state") or not user_input.get("location")
        ):
            errors["identify_by_vehicle_api"] = "identify_by_vehicle_api_requires_roles"

        raw_cards = user_input.pop("cards", [])

        # An inactive vehicle cannot be charged at the wallbox, so it keeps
        # no card. Any card it had is dropped when it is set inactive.
        if not user_input["active"]:
            return (), errors

        cards: list[Card] = []
        seen_uids: set[str] = set()
        for raw in raw_cards:
            uid = normalize_card_uid(raw["uid"])
            if not uid or uid in INVALID_CARD_UIDS:
                errors["cards"] = "invalid_card_uid"
                continue
            if uid in seen_uids or self._active_conflict(uid, own_subentry_id):
                errors["cards"] = "duplicate_card"
                continue
            seen_uids.add(uid)
            cards.append(
                Card(uid=uid, label=raw["label"], type=raw["type"], active=raw.get("active", True))
            )

        if not errors and not cards and not user_input.get("identify_by_vehicle_api"):
            errors["cards"] = "identification_required"

        return tuple(cards), errors

    def _active_conflict(self, uid: str, own_subentry_id: str | None) -> bool:
        """Return whether uid is already held by another active vehicle's card."""
        for subentry in self._entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE):
            if subentry.subentry_id == own_subentry_id:
                continue
            vehicle = Vehicle.from_dict(subentry.data)
            if vehicle.active and any(card.uid == uid for card in vehicle.cards):
                return True
        return False

    async def async_step_charge_state_mapping(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Map the vehicle's raw charge state values onto the four classes (4.7)."""
        entity_id = self._pending.get("charge_state")
        if not entity_id:
            self._pending["charge_state_mapping"] = {}
            return await self.async_step_charge_type_mapping()

        existing = self._subentry_vehicle().charge_state_mapping if self._subentry else {}
        mapping, form = await _async_mapping_step(
            self,
            step_id="charge_state_mapping",
            user_input=user_input,
            entity_id=entity_id,
            preset_role_key="charge_state",
            classes=CHARGE_STATE_CLASSES,
            class_translation_key="charge_state_class",
            existing=existing,
        )
        if form is not None:
            return form
        self._pending["charge_state_mapping"] = mapping
        return await self.async_step_charge_type_mapping()

    async def async_step_charge_type_mapping(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Map the vehicle's raw charge type values onto ac/dc (4.7)."""
        entity_id = self._pending.get("charge_type")
        if not entity_id:
            self._pending["charge_type_mapping"] = {}
            return self._finish()

        existing = self._subentry_vehicle().charge_type_mapping if self._subentry else {}
        mapping, form = await _async_mapping_step(
            self,
            step_id="charge_type_mapping",
            user_input=user_input,
            entity_id=entity_id,
            preset_role_key="charge_type",
            classes=CHARGE_TYPES,
            class_translation_key="charge_type_class",
            existing=existing,
        )
        if form is not None:
            return form
        self._pending["charge_type_mapping"] = mapping
        return self._finish()

    def _subentry_vehicle(self) -> Vehicle:
        assert self._subentry is not None
        return Vehicle.from_dict(self._subentry.data)

    def _finish(self) -> SubentryFlowResult:
        data = self._pending
        vehicle_kwargs = dict(
            name=data["name"],
            active=data["active"],
            is_guest=data["is_guest"],
            vin=data["vin"],
            manufacturer=data["manufacturer"],
            model=data["model"],
            capacity_kwh=data.get("capacity_kwh"),
            cost_mode=data["cost_mode"],
            cards=data["cards"],
            identify_by_vehicle_api=data.get("identify_by_vehicle_api", False),
            soc=resolver.build_role(self.hass, data.get("soc")),
            soc_target=resolver.build_role(self.hass, data.get("soc_target")),
            odometer=resolver.build_role(self.hass, data.get("odometer")),
            charge_state=resolver.build_role(self.hass, data.get("charge_state")),
            charge_state_mapping=data["charge_state_mapping"],
            charge_type=resolver.build_role(self.hass, data.get("charge_type")),
            charge_type_mapping=data["charge_type_mapping"],
            energy_session=resolver.build_role(self.hass, data.get("energy_session")),
            location=resolver.build_role(self.hass, data.get("location")),
            charge_end=resolver.build_role(self.hass, data.get("charge_end")),
            charge_power=resolver.build_role(self.hass, data.get("charge_power")),
            range=resolver.build_role(self.hass, data.get("range")),
        )

        if self._subentry:
            vehicle = Vehicle(id=self._subentry_vehicle().id, **vehicle_kwargs)
            return self.async_update_reload_and_abort(
                self._entry, self._subentry, title=vehicle.name, data=vehicle.to_dict()
            )

        vehicle_id = _allocate_id(
            self._entry, self.hass, sequence_key=CONF_VEHICLE_SEQUENCE, prefix=VEHICLE_ID_PREFIX
        )
        vehicle = Vehicle(id=vehicle_id, **vehicle_kwargs)
        result = self.async_create_entry(title=vehicle.name, data=vehicle.to_dict())
        self.hass.config_entries.async_schedule_reload(self._entry.entry_id)
        return result

    def _schema(self, *, defaults: Vehicle | None) -> vol.Schema:
        d = defaults
        return vol.Schema(
            {
                vol.Required("name", default=d.name if d else vol.UNDEFINED): str,
                vol.Required("active", default=d.active if d else True): bool,
                vol.Required("is_guest", default=d.is_guest if d else False): bool,
                vol.Optional("vin", description={"suggested_value": d.vin if d else None}): str,
                vol.Optional(
                    "manufacturer",
                    description={"suggested_value": d.manufacturer if d else None},
                ): str,
                vol.Optional("model", description={"suggested_value": d.model if d else None}): str,
                vol.Optional(
                    "capacity_kwh",
                    description={"suggested_value": d.capacity_kwh if d else None},
                ): vol.Any(None, vol.Coerce(float)),
                vol.Required(
                    "cost_mode",
                    default=d.cost_mode if d else COST_MODE_DYNAMIC,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(COST_MODES),
                        translation_key="cost_mode",
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    "identify_by_vehicle_api", default=d.identify_by_vehicle_api if d else False
                ): bool,
                vol.Optional(
                    "cards", default=[card.to_dict() for card in d.cards] if d else []
                ): ObjectSelector(
                    ObjectSelectorConfig(
                        multiple=True,
                        label_field="label",
                        translation_key="cards",
                        fields={
                            "uid": {"selector": TextSelector(), "required": True},
                            "label": {"selector": TextSelector(), "required": True},
                            "type": {
                                "selector": SelectSelector(
                                    SelectSelectorConfig(
                                        options=[
                                            SelectOptionDict(value=CARD_TYPE_RFID, label="RFID"),
                                            SelectOptionDict(value=CARD_TYPE_EMAID, label="EMAID"),
                                        ]
                                    )
                                ),
                                "required": True,
                            },
                            "active": {"selector": BooleanSelector(), "required": False},
                        },
                    )
                ),
                vol.Required("roles"): section(
                    vol.Schema(
                        {
                            vol.Optional("soc", default=_entity_id(d.soc) if d else None): vol.Any(
                                None, EntitySelector()
                            ),
                            vol.Optional(
                                "soc_target", default=_entity_id(d.soc_target) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "odometer", default=_entity_id(d.odometer) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "charge_state", default=_entity_id(d.charge_state) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "charge_type", default=_entity_id(d.charge_type) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "energy_session",
                                default=_entity_id(d.energy_session) if d else None,
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "location", default=_entity_id(d.location) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "charge_end", default=_entity_id(d.charge_end) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "charge_power", default=_entity_id(d.charge_power) if d else None
                            ): vol.Any(None, EntitySelector()),
                            vol.Optional(
                                "range", default=_entity_id(d.range) if d else None
                            ): vol.Any(None, EntitySelector()),
                        }
                    ),
                    SectionConfig(collapsed=False),
                ),
            }
        )
