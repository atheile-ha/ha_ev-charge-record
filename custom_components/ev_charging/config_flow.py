"""Config flow for the ev_charging integration."""

from __future__ import annotations

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
    ObjectSelector,
    ObjectSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
)

from .const import (
    CARD_TYPES,
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
    INVALID_CARD_UIDS,
    MAX_IDENTIFICATION_WINDOW_S,
    MAX_START_DEBOUNCE_S,
    MAX_UPDATE_INTERVAL_S,
    MIN_IDENTIFICATION_WINDOW_S,
    MIN_START_DEBOUNCE_S,
    MIN_UPDATE_INTERVAL_S,
    SOLAR_VALUATIONS,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
    VEHICLE_ID_PREFIX,
    WALLBOX_ID_PREFIX,
)
from .models import Card, HubSettings, Vehicle, Wallbox, normalize_card_uid


class EvChargingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ev_charging."""

    VERSION = 2
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
                settings = HubSettings(**user_input)
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
        errors: dict[str, str] = {}

        if user_input is not None:
            expert = user_input.pop("expert")
            user_input.update(expert)
            user_input["manufacturer"] = user_input.get("manufacturer") or None
            user_input["model"] = user_input.get("model") or None
            errors = self._validate(user_input)
            if not errors:
                if subentry:
                    wallbox = Wallbox(id=defaults.id, **user_input)
                    return self.async_update_and_abort(
                        self._entry, subentry, title=wallbox.name, data=wallbox.to_dict()
                    )

                wallbox_id = _allocate_id(
                    self._entry,
                    self.hass,
                    sequence_key=CONF_WALLBOX_SEQUENCE,
                    prefix=WALLBOX_ID_PREFIX,
                )
                wallbox = Wallbox(id=wallbox_id, **user_input)
                return self.async_create_entry(title=wallbox.name, data=wallbox.to_dict())

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
        return errors

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
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input["vin"] = user_input.get("vin") or None
            user_input["manufacturer"] = user_input.get("manufacturer") or None
            user_input["model"] = user_input.get("model") or None
            own_subentry_id = subentry.subentry_id if subentry else None
            cards, errors = self._validate(user_input, own_subentry_id=own_subentry_id)
            if not errors:
                if subentry:
                    vehicle = Vehicle(id=defaults.id, cards=cards, **user_input)
                    return self.async_update_and_abort(
                        self._entry, subentry, title=vehicle.name, data=vehicle.to_dict()
                    )

                vehicle_id = _allocate_id(
                    self._entry,
                    self.hass,
                    sequence_key=CONF_VEHICLE_SEQUENCE,
                    prefix=VEHICLE_ID_PREFIX,
                )
                vehicle = Vehicle(id=vehicle_id, cards=cards, **user_input)
                return self.async_create_entry(title=vehicle.name, data=vehicle.to_dict())

        return self.async_show_form(
            step_id=step_id, data_schema=self._schema(defaults=defaults), errors=errors
        )

    def _validate(
        self, user_input: dict[str, Any], *, own_subentry_id: str | None
    ) -> tuple[tuple[Card, ...], dict[str, str]]:
        errors: dict[str, str] = {}
        if not user_input.get("is_guest") and user_input.get("capacity_kwh") is None:
            errors["capacity_kwh"] = "capacity_required"

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

        if not errors and not cards:
            errors["cards"] = "card_required"

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
                    SelectSelectorConfig(options=list(COST_MODES), translation_key="cost_mode")
                ),
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
                                        options=list(CARD_TYPES), translation_key="card_type"
                                    )
                                ),
                                "required": True,
                            },
                            "active": {"selector": BooleanSelector(), "required": False},
                        },
                    )
                ),
            }
        )
