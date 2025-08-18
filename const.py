"""Constants for the Integration 101 Template integration."""
from homeassistant.const import Platform

DOMAIN = "pid_departure_board"
PLATFORMS: list[Platform] = [Platform.SENSOR]

DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 10
