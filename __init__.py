"""PID Departure Board integration."""

from __future__ import annotations


from homeassistant.core import HomeAssistant


from .const import PLATFORMS
from .models import RuntimeData, PidConfigEntry





async def async_setup_entry(hass: HomeAssistant, config_entry: PidConfigEntry) -> bool:
    # Populate typed runtime data for use by platforms
    config_entry.runtime_data = RuntimeData(
        api_key=config_entry.data["api_key"],
        stop_ids=config_entry.data["stop_ids"],
    )

    # This calls the async_setup method in each of your entity type files.
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Return true to denote a successful setup.
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: PidConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
