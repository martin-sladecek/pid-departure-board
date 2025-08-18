"""Interfaces with the Integration 101 Template api sensors."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
import logging

from .const import DOMAIN
from .api import GolemioAPI, GolemioCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    api_key = entry.data["api_key"]
    stop_ids = entry.data["stop_ids"]

    api = GolemioAPI(api_key)

    entities = []
    coordinator = GolemioCoordinator(hass, api, stop_ids)
    await coordinator.async_config_entry_first_refresh()
    for stop_id in stop_ids:
        entities.append(PidStopSensor(coordinator, stop_id))
    async_add_entities(entities)

def flatten_dict(d, parent_key="", sep="_"):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


class PidStopSensor(SensorEntity):

    def __init__(self, coordinator, stop_id):
        self.coordinator = coordinator
        self.stop_id = stop_id
        self.stop_name = self.coordinator.data[self.stop_id]["stop"]["stop_name"]
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, stop_id)},
                                            name=f"{self.stop_name} Stop",
                                            entry_type=DeviceEntryType.SERVICE)

    @property
    def name(self):
        return f"{self.stop_name} Departures"

    @property
    def unique_id(self):
        return f"{self.stop_id}_departures"

    @property
    def extra_state_attributes(self):
        attrs = {}
        departures = [flatten_dict(x) for x in self.coordinator.data[self.stop_id].get("departures", [])]
        attrs["stop_name"] = self.coordinator.data[self.stop_id]["stop"]["stop_name"]
        attrs["departures"] = departures
        return attrs

    async def async_update(self):
        await self.coordinator.async_request_refresh()