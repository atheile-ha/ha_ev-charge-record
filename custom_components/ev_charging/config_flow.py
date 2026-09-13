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
    CONF_VEHICLE_SEQUENCE,
    CONF_WALLBOX_SEQUENCE,
    COST_MODE_DYNAMIC,
    COST_MODE_STATIC,
    COST_MODES,
    CURRENT_TYPE_AC,
    CURRENT_TYPES,
    DEFAULT_POWER_THRESHOLD_KW,
    DEFAULT_START_DEBOUNCE_S,
    DOMAIN,
    MAX_START_DEBOUNCE_S,
    MIN_START_DEBOUNCE_S,
    SOLAR_VALUATION_FEED_IN_TARIFF,
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
            expert = user_input.pop("expert")
            user_input.update(expert)
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
                        }
                    ),
                    SectionConfig(collapsed=True),
                ),
            }
        )


class VehicleSubentryFlow(ConfigSubentryFlow):
    """Handle creating and editing a vehicle subentry, including its cards.

    Name, guest/active status, capacity, cards and the cost mode choice are
    entered on a single form. Only the cost mode's follow-up field (a fixed
    price, or the solar valuation) is a separate step, because which one
    applies depends on the choice made on the first form.
    """

    def __init__(self) -> None:
        """Initialize the state carried from the base step to the cost step."""
        self._base_data: dict[str, Any] = {}
        self._cards: tuple[Card, ...] = ()
        self._subentry: ConfigSubentry | None = None

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
            own_subentry_id = subentry.subentry_id if subentry else None
            cards, errors = self._validate_base(user_input, own_subentry_id=own_subentry_id)
            if not errors:
                self._base_data = user_input
                self._cards = cards
                self._subentry = subentry
                if user_input["cost_mode"] == COST_MODE_STATIC:
                    return await self.async_step_static_price()
                return await self.async_step_solar_valuation()

        return self.async_show_form(
            step_id=step_id, data_schema=self._base_schema(defaults=vehicle), errors=errors
        )

    def _validate_base(
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
            if uid in seen_uids or self._active_conflict(uid, own_subentry_id):
                errors["cards"] = "duplicate_card"
                continue
            seen_uids.add(uid)
            cards.append(Card(uid=uid, label=raw["label"], active=raw.get("active", True)))

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
                            "active": {"selector": BooleanSelector(), "required": False},
                        },
                    )
                ),
            }
        )

    async def async_step_static_price(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Ask for the fixed price that applies to the whole charge."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get("static_price") is None:
                errors["static_price"] = "static_price_required"
            else:
                return self._finish(
                    static_price=user_input["static_price"],
                    solar_valuation=SOLAR_VALUATION_FEED_IN_TARIFF,
                )

        existing = self._existing_vehicle
        suggested = (
            existing.static_price if existing and existing.cost_mode == COST_MODE_STATIC else None
        )
        schema = vol.Schema(
            {
                vol.Optional("static_price", description={"suggested_value": suggested}): vol.Any(
                    None, vol.Coerce(float)
                ),
            }
        )
        return self.async_show_form(step_id="static_price", data_schema=schema, errors=errors)

    async def async_step_solar_valuation(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Ask how the solar share of a home charge is valued."""
        if user_input is not None:
            return self._finish(static_price=None, solar_valuation=user_input["solar_valuation"])

        existing = self._existing_vehicle
        default = (
            existing.solar_valuation
            if existing and existing.cost_mode == COST_MODE_DYNAMIC
            else SOLAR_VALUATION_FEED_IN_TARIFF
        )
        schema = vol.Schema(
            {
                vol.Required("solar_valuation", default=default): SelectSelector(
                    SelectSelectorConfig(
                        options=list(SOLAR_VALUATIONS), translation_key="solar_valuation"
                    )
                ),
            }
        )
        return self.async_show_form(step_id="solar_valuation", data_schema=schema)

    @property
    def _existing_vehicle(self) -> Vehicle | None:
        """Return the vehicle being reconfigured, if any."""
        return Vehicle.from_dict(self._subentry.data) if self._subentry else None

    def _finish(self, *, static_price: float | None, solar_valuation: str) -> SubentryFlowResult:
        """Persist the vehicle with the base data and the chosen cost fields."""
        vehicle_data = {
            **self._base_data,
            "static_price": static_price,
            "solar_valuation": solar_valuation,
        }

        if self._subentry:
            vehicle = Vehicle(id=self._existing_vehicle.id, cards=self._cards, **vehicle_data)
            return self.async_update_and_abort(
                self._entry, self._subentry, title=vehicle.name, data=vehicle.to_dict()
            )

        vehicle_id = _allocate_id(
            self._entry, self.hass, sequence_key=CONF_VEHICLE_SEQUENCE, prefix=VEHICLE_ID_PREFIX
        )
        vehicle = Vehicle(id=vehicle_id, cards=self._cards, **vehicle_data)
        return self.async_create_entry(title=vehicle.name, data=vehicle.to_dict())
