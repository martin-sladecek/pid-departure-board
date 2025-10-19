"""Constants for the PID Departure Board integration."""
from homeassistant.const import Platform

DOMAIN = "pid_departure_board"
PLATFORMS: list[Platform] = [Platform.SENSOR]
DEFAULT_MINUTES_BEFORE = 0
DEFAULT_MINUTES_AFTER = 60
