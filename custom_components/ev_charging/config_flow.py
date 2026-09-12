"""Config flow for the ev_charging integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentry,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import (
    CONF_VEHICLE_SEQUENCE,
    CONF_WALLBOX_SEQUENCE,
    CURRENT_TYPE_AC,
    CURRENT_TYPES,
    DEFAULT_ERROR_DEBOUNCE_S,
    DEFAULT_FINAL_VALUES_GRACE_MIN,
    DEFAULT_IDENTIFICATION_MAX_AGE_MIN,
    DEFAULT_MIN_PAUSE_MIN,
    DEFAULT_POWER_THRESHOLD_KW,
    DEFAULT_SESSION_END_PAUSE_MIN,
    DEFAULT_SESSION_STALE_H,
    DEFAULT_START_DEBOUNCE_S,
    DOMAIN,
    MAX_START_DEBOUNCE_S,
    MIN_START_DEBOUNCE_S,
    SESSION_STRATEGIES,
    SESSION_STRATEGY_PLUG_STATE,
    SESSION_STRATEGY_POWER_PAUSE,
    SOLAR_VALUATION_FEED_IN_TARIFF,
    SOLAR_VALUATION_FIXED,
    SOLAR_VALUATIONS,
    SUBENTRY_TYPE_VEHICLE,
    SUBENTRY_TYPE_WALLBOX,
    TITLE,
    VEHICLE_ID_PREFIX,
    WALLBOX_ID_PREFIX,
)
from .models import Card, Vehicle, Wallbox, normalize_card_uid


class EvChargingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ev_charging."""

    VERSION = 1
    MINOR_VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm the setup. The entry carries no options yet."""
        if user_input is None:
            return self.async_show_form(step_id="user")

        return self.async_create_entry(
            title=TITLE,
            data={CONF_WALLBOX_SEQUENCE: 0, CONF_VEHICLE_SEQUENCE: 0},
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
            errors = self._validate(user_input)
            if not errors:
                if user_input["session_strategy"] != SESSION_STRATEGY_POWER_PAUSE:
                    user_input["session_end_pause_min"] = None

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
        if user_input["max_power_kw"] <= 0:
            errors["max_power_kw"] = "must_be_positive"
        for key in (
            "power_threshold_kw",
            "min_pause_min",
            "session_end_pause_min",
            "final_values_grace_min",
            "identification_max_age_min",
            "error_debounce_s",
            "session_stale_h",
        ):
            if user_input.get(key, 0) < 0:
                errors[key] = "must_not_be_negative"
        return errors

    def _schema(self, *, defaults: Wallbox | None) -> vol.Schema:
        d = defaults
        vehicle_options = [
            SelectOptionDict(value=vehicle.id, label=vehicle.name)
            for vehicle in (
                Vehicle.from_dict(subentry.data)
                for subentry in self._entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)
            )
        ]

        fields: dict[Any, Any] = {
            vol.Required("name", default=d.name if d else vol.UNDEFINED): str,
            vol.Required(
                "current_type", default=d.current_type if d else CURRENT_TYPE_AC
            ): SelectSelector(
                SelectSelectorConfig(options=list(CURRENT_TYPES), translation_key="current_type")
            ),
            vol.Required(
                "max_power_kw", default=d.max_power_kw if d else vol.UNDEFINED
            ): vol.Coerce(float),
            vol.Required(
                "session_strategy",
                default=d.session_strategy if d else SESSION_STRATEGY_PLUG_STATE,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=list(SESSION_STRATEGIES), translation_key="session_strategy"
                )
            ),
            vol.Required(
                "power_threshold_kw",
                default=d.power_threshold_kw if d else DEFAULT_POWER_THRESHOLD_KW,
            ): vol.Coerce(float),
            vol.Required(
                "start_debounce_s",
                default=d.start_debounce_s if d else DEFAULT_START_DEBOUNCE_S,
            ): vol.Coerce(int),
            vol.Required(
                "min_pause_min", default=d.min_pause_min if d else DEFAULT_MIN_PAUSE_MIN
            ): vol.Coerce(int),
            vol.Required(
                "session_end_pause_min",
                default=(
                    d.session_end_pause_min
                    if d and d.session_end_pause_min is not None
                    else DEFAULT_SESSION_END_PAUSE_MIN
                ),
            ): vol.Coerce(int),
            vol.Required(
                "final_values_grace_min",
                default=d.final_values_grace_min if d else DEFAULT_FINAL_VALUES_GRACE_MIN,
            ): vol.Coerce(int),
            vol.Required(
                "identification_max_age_min",
                default=d.identification_max_age_min if d else DEFAULT_IDENTIFICATION_MAX_AGE_MIN,
            ): vol.Coerce(int),
            vol.Required(
                "error_debounce_s",
                default=d.error_debounce_s if d else DEFAULT_ERROR_DEBOUNCE_S,
            ): vol.Coerce(int),
            vol.Required(
                "session_stale_h", default=d.session_stale_h if d else DEFAULT_SESSION_STALE_H
            ): vol.Coerce(int),
        }

        if vehicle_options:
            fields[
                vol.Optional(
                    "default_vehicle_id",
                    description={"suggested_value": d.default_vehicle_id if d else None},
                )
            ] = vol.Any(None, SelectSelector(SelectSelectorConfig(options=vehicle_options)))

        return vol.Schema(fields)


class VehicleSubentryFlow(ConfigSubentryFlow):
    """Handle creating and editing a vehicle subentry, including its cards."""

    def __init__(self) -> None:
        """Initialize the working state accumulated across the flow's steps."""
        self._vehicle_data: dict[str, Any] = {}
        self._cards: list[Card] = []
        self._own_subentry_id: str | None = None
        self._selected_card_uid: str | None = None

    @property
    def _entry(self) -> ConfigEntry:
        return self.hass.config_entries.async_get_known_entry(self.handler[0])

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Create a new vehicle subentry."""
        return await self._async_step_base(user_input, subentry=None)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Edit an existing vehicle subentry."""
        return await self._async_step_base(user_input, subentry=self._get_reconfigure_subentry())

    async def _async_step_base(
        self, user_input: dict[str, Any] | None, *, subentry: ConfigSubentry | None
    ) -> SubentryFlowResult:
        step_id = "reconfigure" if subentry else "user"
        vehicle = Vehicle.from_dict(subentry.data) if subentry else None
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input["vin"] = user_input.get("vin") or None
            errors = self._validate_base(user_input)
            if not errors:
                self._vehicle_data = user_input
                self._cards = list(vehicle.cards) if vehicle else []
                self._own_subentry_id = subentry.subentry_id if subentry else None
                return await self.async_step_cards_menu()

        return self.async_show_form(
            step_id=step_id, data_schema=self._base_schema(defaults=vehicle), errors=errors
        )

    def _validate_base(self, user_input: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}
        if not user_input.get("is_guest") and user_input.get("capacity_kwh") is None:
            errors["capacity_kwh"] = "capacity_required"
        if (
            user_input.get("solar_valuation") == SOLAR_VALUATION_FIXED
            and user_input.get("solar_valuation_fixed") is None
        ):
            errors["solar_valuation_fixed"] = "fixed_valuation_required"
        return errors

    def _base_schema(self, *, defaults: Vehicle | None) -> vol.Schema:
        d = defaults
        return vol.Schema(
            {
                vol.Required("name", default=d.name if d else vol.UNDEFINED): str,
                vol.Required("active", default=d.active if d else True): bool,
                vol.Required("is_guest", default=d.is_guest if d else False): bool,
                vol.Optional("vin", description={"suggested_value": d.vin if d else None}): str,
                vol.Optional(
                    "capacity_kwh",
                    description={"suggested_value": d.capacity_kwh if d else None},
                ): vol.Any(None, vol.Coerce(float)),
                vol.Required(
                    "solar_valuation",
                    default=d.solar_valuation if d else SOLAR_VALUATION_FEED_IN_TARIFF,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(SOLAR_VALUATIONS), translation_key="solar_valuation"
                    )
                ),
                vol.Optional(
                    "solar_valuation_fixed",
                    description={"suggested_value": d.solar_valuation_fixed if d else None},
                ): vol.Any(None, vol.Coerce(float)),
            }
        )

    async def async_step_cards_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Offer to add a card, edit an existing one, or finish."""
        options = ["add_card"]
        if self._cards:
            options.append("select_card")
        options.append("finish")
        return self.async_show_menu(step_id="cards_menu", menu_options=options)

    async def async_step_add_card(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a new card to the vehicle being edited."""
        errors: dict[str, str] = {}
        if user_input is not None:
            uid = normalize_card_uid(user_input["uid"])
            if any(card.uid == uid for card in self._cards) or (
                self._vehicle_data.get("active", True) and self._active_conflict(uid)
            ):
                errors["uid"] = "duplicate_card"
            else:
                self._cards.append(
                    Card(uid=uid, label=user_input["label"], active=user_input.get("active", True))
                )
                return await self.async_step_cards_menu()

        schema = vol.Schema(
            {
                vol.Required("uid"): str,
                vol.Required("label"): str,
                vol.Optional("active", default=True): bool,
            }
        )
        return self.async_show_form(step_id="add_card", data_schema=schema, errors=errors)

    def _active_conflict(self, uid: str) -> bool:
        """Return whether uid is already held by another active vehicle's card."""
        for subentry in self._entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE):
            if subentry.subentry_id == self._own_subentry_id:
                continue
            vehicle = Vehicle.from_dict(subentry.data)
            if vehicle.active and any(card.uid == uid for card in vehicle.cards):
                return True
        return False

    async def async_step_select_card(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Pick one of the vehicle's existing cards to edit or remove."""
        if user_input is not None:
            self._selected_card_uid = user_input["uid"]
            return await self.async_step_edit_card()

        schema = vol.Schema(
            {
                vol.Required("uid"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=card.uid, label=f"{card.label} ({card.uid})")
                            for card in self._cards
                        ]
                    )
                )
            }
        )
        return self.async_show_form(step_id="select_card", data_schema=schema)

    async def async_step_edit_card(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Edit the label and lock state of the selected card, or remove it."""
        current = next(card for card in self._cards if card.uid == self._selected_card_uid)

        if user_input is not None:
            if user_input.get("remove"):
                self._cards = [card for card in self._cards if card.uid != current.uid]
            else:
                self._cards = [
                    Card(uid=current.uid, label=user_input["label"], active=user_input["active"])
                    if card.uid == current.uid
                    else card
                    for card in self._cards
                ]
            return await self.async_step_cards_menu()

        schema = vol.Schema(
            {
                vol.Required("label", default=current.label): str,
                vol.Required("active", default=current.active): bool,
                vol.Optional("remove", default=False): bool,
            }
        )
        return self.async_show_form(
            step_id="edit_card",
            data_schema=schema,
            description_placeholders={"uid": current.uid},
        )

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Persist the vehicle with the cards accumulated in this flow."""
        entry = self._entry

        if self.source == SOURCE_RECONFIGURE:
            subentry = self._get_reconfigure_subentry()
            vehicle = Vehicle(
                id=Vehicle.from_dict(subentry.data).id,
                cards=tuple(self._cards),
                **self._vehicle_data,
            )
            return self.async_update_and_abort(
                entry, subentry, title=vehicle.name, data=vehicle.to_dict()
            )

        vehicle_id = _allocate_id(
            entry, self.hass, sequence_key=CONF_VEHICLE_SEQUENCE, prefix=VEHICLE_ID_PREFIX
        )
        vehicle = Vehicle(id=vehicle_id, cards=tuple(self._cards), **self._vehicle_data)
        return self.async_create_entry(title=vehicle.name, data=vehicle.to_dict())
