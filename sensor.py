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
    coordinator = GolemioCoordinator(
        hass,
        api,
        stop_ids,
        entry.runtime_data.minutes_before,
        entry.runtime_data.minutes_after,
    )
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
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, stop_id)},
                                            name=f"{self._current_stop_name()} Stop",
                                            entry_type=DeviceEntryType.SERVICE)

    def _stop_payload(self):
        stop_data = self.coordinator.data.get(self.stop_id, {}).get("stop", {})
        return stop_data if isinstance(stop_data, dict) else {}

    def _current_stop_name(self):
        stop_data = self._stop_payload()
        return stop_data.get("stop_name") or self.stop_id

    def _departure_datetime(self, departure):
        if not isinstance(departure, dict):
            return None
        timestamp = departure.get("departure_timestamp", {})
        if not isinstance(timestamp, dict):
            return None
        raw_ts = timestamp.get("predicted") or timestamp.get("aimed")
        if not raw_ts:
            return None
        dt = dt_util.parse_datetime(raw_ts)
        if not dt:
            return None
        return dt_util.as_utc(dt)

    @property
    def name(self):
        return f"{self._current_stop_name()} Departures"

    @property
    def unique_id(self):
        return f"{self.stop_id}_departures"

    @property
    def extra_state_attributes(self):
        attrs = {}
        stop_entry = self.coordinator.data.get(self.stop_id, {})
        raw_departures = stop_entry.get("departures", [])
        departures = [flatten_dict(x) for x in raw_departures if isinstance(x, dict)]
        infotexts = stop_entry.get("infotexts", [])
        attrs["stop_name"] = self._current_stop_name()
        attrs["departures"] = departures
        attrs["infotexts"] = infotexts if isinstance(infotexts, list) else []
        return attrs

    @property
    def native_value(self):
        departures = self.coordinator.data.get(self.stop_id, {}).get("departures", [])
        if not departures:
            return None
        valid_departures = sorted(
            (dt for dt in (self._departure_datetime(dep) for dep in departures) if dt is not None)
        )
        if not valid_departures:
            return None
        return valid_departures[0]
