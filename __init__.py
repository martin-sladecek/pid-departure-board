"""PID Departure Board integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import PLATFORMS, DEFAULT_MINUTES_BEFORE, DEFAULT_MINUTES_AFTER
from .models import RuntimeData, PidConfigEntry


async def async_setup_entry(hass: HomeAssistant, config_entry: PidConfigEntry) -> bool:
    # Populate typed runtime data for use by platforms
    # Prefer stop_ids from options (editable via Options Flow), fallback to data for backward compatibility
    stop_ids = config_entry.options.get("stop_ids", config_entry.data["stop_ids"])
    minutes_before = config_entry.options.get("minutes_before", DEFAULT_MINUTES_BEFORE)
    minutes_after = config_entry.options.get("minutes_after", DEFAULT_MINUTES_AFTER)
    config_entry.runtime_data = RuntimeData(
        api_key=config_entry.data["api_key"],
        stop_ids=stop_ids,
        minutes_before=minutes_before,
        minutes_after=minutes_after,
    )

    # Reload the entry when options (e.g., stop_ids) change
    config_entry.async_on_unload(
        config_entry.add_update_listener(async_update_listener)
    )

    # This calls the async_setup method in each of your entity type files.
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Return true to denote a successful setup.
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: PidConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_update_listener(hass: HomeAssistant, entry: PidConfigEntry) -> None:
    # Reload the config entry to apply updated options
    await hass.config_entries.async_reload(entry.entry_id)
