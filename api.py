from datetime import timedelta

import aiohttp
import async_timeout
import logging
from multidict import MultiDict

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class GolemioAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    async def get_departures(self, stop_ids: list[str]):
        headers = {"x-access-token": self.api_key}
        params = MultiDict([("ids[]", v) for v in stop_ids])
        params.merge({"minutesBefore": 0, "minutesAfter": 60})
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.get(
                    "https://api.golemio.cz/v2/pid/departureboards",
                    headers=headers,
                    params=params
                ) as resp:
                    resp.raise_for_status()
                    return await resp.json()


class GolemioCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, stop_ids: list[str]):
        super().__init__(
            hass,
            _LOGGER,
            name=f"golemio",
            update_interval=timedelta(seconds=30)
        )
        self.api = api
        self.stop_ids = stop_ids

    def group_by_stop_id(self, data):
        result = {}
        for stop in data.get("stops", []):
            stop_id = stop["stop_id"]
            result[stop_id] = {
                "stop": stop,
                "departures": [],
                "infotexts": []
            }
            for dep in data.get("departures", []):
                if dep.get("stop", {}).get("id") == stop_id:
                    result[stop_id]["departures"].append(dep)
            for info in data.get("infotexts", []):
                if stop_id in info.get("related_stops", []):
                    result[stop_id]["infotexts"].append(info)
        return result

    async def _async_update_data(self):
        try:
            data = await self.api.get_departures(self.stop_ids)
            return self.group_by_stop_id(data)
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")
