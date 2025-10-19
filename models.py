from __future__ import annotations

import dataclasses
from homeassistant.config_entries import ConfigEntry


@dataclasses.dataclass
class RuntimeData:
    """Runtime data stored on the config entry."""
    api_key: str
    stop_ids: list[str]
    minutes_before: int
    minutes_after: int


type PidConfigEntry = ConfigEntry[RuntimeData]
