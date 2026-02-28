import voluptuous as vol
import aiohttp
import asyncio

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.config_entries import OptionsFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import GolemioAPI
from .const import DOMAIN, DEFAULT_MINUTES_BEFORE, DEFAULT_MINUTES_AFTER


def normalize_stop_ids(raw: object) -> list[str]:
    if isinstance(raw, list):
        values = raw
    else:
        values = str(raw).split(",")

    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        stop_id = value.strip()
        if not stop_id or stop_id in seen:
            continue
        seen.add(stop_id)
        normalized.append(stop_id)
    return normalized


class PidConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            api_key = user_input["api_key"].strip()
            if not api_key:
                errors["api_key"] = "missing_api_key"
            else:
                stop_ids = normalize_stop_ids(user_input["stop_ids"])
                if not stop_ids:
                    errors["stop_ids"] = "invalid_stop_ids"
                else:
                    api = GolemioAPI(async_get_clientsession(self.hass), api_key)
                    try:
                        data = await api.get_stops(stop_ids)
                    except aiohttp.ClientResponseError as err:
                        if err.status in (401, 403):
                            errors["base"] = "invalid_auth"
                        elif err.status in (400, 404, 422):
                            errors["stop_ids"] = "invalid_stop_ids"
                        else:
                            errors["base"] = "cannot_connect"
                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        errors["base"] = "cannot_connect"
                    else:
                        valid_stop_ids = {
                            feature.get("properties", {}).get("stop_id")
                            for feature in data.get("features", [])
                            if isinstance(feature, dict)
                            and isinstance(feature.get("properties"), dict)
                            and feature.get("properties", {}).get("stop_id")
                        }

                        if not valid_stop_ids or not set(stop_ids).issubset(valid_stop_ids):
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
            stop_ids = normalize_stop_ids(user_input["stop_ids"])

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
            vol.Optional("minutes_before", default=current_before): NumberSelector(
                NumberSelectorConfig(min=-4320, max=30, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional("minutes_after", default=current_after): NumberSelector(
                NumberSelectorConfig(min=-4350, max=4320, step=1, mode=NumberSelectorMode.BOX)
            ),
        })
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, {"stop_ids": default_list}),
            errors=errors
        )
