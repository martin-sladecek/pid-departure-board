# PID Departure Board – Home Assistant Custom Integration

Show upcoming departures from Prague Integrated Transport (PID) stops directly in Home Assistant. Data is fetched from the Golemio API and exposed as one sensor per configured stop.

- One sensor entity per stop ID
- Attributes include stop_name and a list of upcoming departures
- Updates every ~30 seconds via a DataUpdateCoordinator

## Requirements

- A Golemio (PID) API key
  - Get one from: https://api.golemio.cz/api-keys/dashboard
- PID stop IDs you want to monitor (comma-separated)
  - You can obtain stop IDs from [PID datasets](https://opendata.praha.eu/datasets/https%3A%2F%2Fapi.opendata.praha.eu%2Flod%2Fcatalog%2F9a6a1d8e-45b9-41de-b9ae-0bcec7126876) or [Golemio API](https://api.golemio.cz/pid/docs/openapi/#/). The IDs should correspond to PID stop identifiers.

## Installation

Manual install:
1. Copy this repository’s directory into your Home Assistant config at:
   `<config>/custom_components/pid_departure_board`
2. Restart Home Assistant.
3. Go to Settings → Devices & Services → Integrations → Add Integration → search for “PID Departure Boards”.

Repository: https://github.com/martin-sladecek/pid-departure-board

## Configuration

When adding the integration via the UI, you will be prompted for:
- PID API key
- Stop IDs (comma separated), for example: `U1234,U5678`

The integration creates:
- A sensor entity for each stop ID.
- Unique ID pattern: `<stop_id>_departures`
- Name pattern: `<Stop Name> Departures`

## Entity Attributes

Each sensor exposes:
- `stop_name`: Human-readable stop name from the API.
- `departures`: A list of departures as flattened key/value dictionaries derived from the Golemio response. Keys mirror Golemio fields (nested fields are flattened with `_`).
- `infotexts`: A list of infotexts (service announcements, disruptions, etc.) related to the stop, preserving the original structure.

Note: The departures are intentionally flattened for flexible use in templates, dashboards, and automations. Infotexts preserve their original structure for easier access to specific fields like validity periods and multilingual text.

## Update Interval

- The integration polls the API approximately every 30 seconds (hard-coded in the coordinator).

## Disclaimer

This project is not affiliated with PID or Golemio. Use of the API is subject to Golemio’s terms and rate limits.
