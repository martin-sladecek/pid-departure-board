"""The Integration 101 Template integration."""

from __future__ import annotations

import dataclasses
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, PLATFORMS


type MyConfigEntry = ConfigEntry[RuntimeData]

@dataclasses.dataclass
class RuntimeData:
    """Class to hold your data."""

    stop_ids: list[str]


async def async_setup_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        "api_key": config_entry.data["api_key"],
        "stop_ids": config_entry.data["stop_ids"],
    }

    # This calls the async_setup method in each of your entity type files.
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Return true to denote a successful setup.
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
