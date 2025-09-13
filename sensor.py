"""Sensors for PID Departure Board integration."""

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .api import GolemioAPI, GolemioCoordinator
from .models import PidConfigEntry

async def async_setup_entry(hass: HomeAssistant, entry: PidConfigEntry, async_add_entities: AddEntitiesCallback):
    api_key = entry.runtime_data.api_key
    stop_ids = entry.runtime_data.stop_ids

    api = GolemioAPI(async_get_clientsession(hass), api_key)

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


class PidStopSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, stop_id):
        super().__init__(coordinator)
        self.stop_id = stop_id
        self.stop_name = self.coordinator.data[self.stop_id]["stop"]["stop_name"]
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
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

    @property
    def native_value(self):
        departures = self.coordinator.data[self.stop_id].get("departures", [])
        if not departures:
            return None
        ts = departures[0].get("departure_timestamp",{}).get("predicted")
        if not ts:
            return None
        dt = dt_util.parse_datetime(ts)
        if dt:
            dt = dt_util.as_utc(dt)
        return dt

