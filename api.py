from datetime import timedelta

import aiohttp
from async_timeout import timeout
import logging
import asyncio
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class GolemioAPI:
    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        self.session = session
        self.api_key = api_key

    async def get_departures(self, stop_ids: list[str], minutes_before: int, minutes_after: int) -> dict[str, Any]:
        headers = {"x-access-token": self.api_key}
        params = [("ids[]", v) for v in stop_ids]
        params += [("minutesBefore", minutes_before), ("minutesAfter", minutes_after)]
        async with timeout(10):
            async with self.session.get(
                "https://api.golemio.cz/v2/pid/departureboards",
                headers=headers,
                params=params,
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_stops(self, stop_ids: list[str]) -> dict[str, Any]:
        headers = {"x-access-token": self.api_key}
        params = [("ids[]", v) for v in stop_ids]
        async with timeout(10):
            async with self.session.get(
                "https://api.golemio.cz/v2/gtfs/stops",
                headers=headers,
                params=params,
            ) as resp:
                resp.raise_for_status()
                return await resp.json()


class GolemioCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, stop_ids: list[str], minutes_before: int, minutes_after: int):
        super().__init__(
            hass,
            _LOGGER,
            name=f"golemio",
            update_interval=timedelta(seconds=30)
        )
        self.api = api
        self.stop_ids = stop_ids
        self.minutes_before = minutes_before
        self.minutes_after = minutes_after

    def group_by_stop_id(self, data: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {
            stop_id: {
                "stop": {"stop_id": stop_id, "stop_name": stop_id},
                "departures": [],
                "infotexts": [],
            }
            for stop_id in self.stop_ids
        }

        for stop in data.get("stops", []):
            if not isinstance(stop, dict):
                continue
            stop_id = stop.get("stop_id")
            if stop_id in result:
                result[stop_id]["stop"] = stop

        for dep in data.get("departures", []):
            if not isinstance(dep, dict):
                continue
            stop_id = dep.get("stop", {}).get("id")
            if stop_id in result:
                result[stop_id]["departures"].append(dep)

        for info in data.get("infotexts", []):
            if not isinstance(info, dict):
                continue
            for stop_id in info.get("related_stops", []):
                if stop_id in result:
                    result[stop_id]["infotexts"].append(info)

        return result

    async def _async_update_data(self):
        try:
            data = await self.api.get_departures(self.stop_ids, self.minutes_before, self.minutes_after)
            return self.group_by_stop_id(data)
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(f"HTTP {err.status} while fetching {err.request_info.real_url}: {err.message}")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Error fetching data: {err}")
