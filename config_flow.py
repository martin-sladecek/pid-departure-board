import voluptuous as vol

from homeassistant import config_entries
from .const import DOMAIN


class PidConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            api_key = user_input["api_key"].strip()
            if not api_key:
                errors["api_key"] = "missing_api_key"
            else:
                return self.async_create_entry(
                    title="PID Departure Board",
                    data={"api_key": api_key, "stop_ids": user_input["stop_ids"].split(",")},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("api_key"): str,
                vol.Required("stop_ids", default=""): str
            }),
            errors=errors
        )

    async def async_step_import(self, user_input):
        return await self.async_step_user(user_input)