import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.config_entries import OptionsFlow
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType
from .const import DOMAIN, DEFAULT_MINUTES_BEFORE, DEFAULT_MINUTES_AFTER


class PidConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            api_key = user_input["api_key"].strip()
            if not api_key:
                errors["api_key"] = "missing_api_key"
            else:
                stop_in = user_input["stop_ids"]
                if isinstance(stop_in, list):
                    stop_ids = [s.strip() for s in stop_in if isinstance(s, str) and s.strip()]
                else:
                    stop_ids = [s.strip() for s in str(stop_in).split(",") if s.strip()]
                if not stop_ids:
                    errors["stop_ids"] = "invalid_stop_ids"
                else:
                    return self.async_create_entry(
                        title="PID Departure Board",
                        data={"api_key": api_key, "stop_ids": stop_ids},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("api_key"): str,
                vol.Required("stop_ids", default=[]): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT, multiple=True))
            }),
            errors=errors
        )

    async def async_step_import(self, user_input):
        return await self.async_step_user(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PidOptionsFlowHandler(config_entry)


class PidOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            stop_in = user_input["stop_ids"]
            if isinstance(stop_in, list):
                stop_ids = [s.strip() for s in stop_in if isinstance(s, str) and s.strip()]
            else:
                stop_ids = [s.strip() for s in str(stop_in).split(",") if s.strip()]

            minutes_before = user_input.get("minutes_before", DEFAULT_MINUTES_BEFORE)
            minutes_after = user_input.get("minutes_after", DEFAULT_MINUTES_AFTER)

            try:
                minutes_before = int(minutes_before)
            except (TypeError, ValueError):
                errors["minutes_before"] = "invalid_minutes_before"

            try:
                minutes_after = int(minutes_after)
            except (TypeError, ValueError):
                errors["minutes_after"] = "invalid_minutes_after"

            if not stop_ids:
                errors["stop_ids"] = "invalid_stop_ids"
            else:
                if "minutes_before" not in errors:
                    if minutes_before < -4320 or minutes_before > 30:
                        errors["minutes_before"] = "invalid_minutes_before"
                if "minutes_after" not in errors:
                    if minutes_after < -4350 or minutes_after > 4320:
                        errors["minutes_after"] = "invalid_minutes_after"
                if "minutes_before" not in errors and "minutes_after" not in errors:
                    if (minutes_before + minutes_after) <= 0:
                        errors["base"] = "invalid_interval_sum"

            if not errors:
                return self.async_create_entry(
                    data={
                        "stop_ids": stop_ids,
                        "minutes_before": minutes_before,
                        "minutes_after": minutes_after,
                    }
                )

        current = self.config_entry.options.get("stop_ids", self.config_entry.data.get("stop_ids", []))
        default_list = current if isinstance(current, list) else ([str(current)] if current else [])
        current_before = self.config_entry.options.get("minutes_before", DEFAULT_MINUTES_BEFORE)
        current_after = self.config_entry.options.get("minutes_after", DEFAULT_MINUTES_AFTER)
        schema = vol.Schema({
            vol.Required("stop_ids"): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT, multiple=True)),
            vol.Optional("minutes_before", default=current_before): int,
            vol.Optional("minutes_after", default=current_after): int,
        })
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, {"stop_ids": default_list}),
            errors=errors
        )
