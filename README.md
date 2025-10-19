# PID Departure Board – Home Assistant Custom Integration

Display upcoming departures from Prague Integrated Transport (PID) stops directly in Home Assistant. Data is fetched from the Golemio API and exposed as one sensor entity per configured stop.

Repository: https://github.com/martin-sladecek/pid-departure-board

## Features

- One sensor entity per PID stop ID
- State is the next predicted departure time (device class: timestamp)
- Attributes include:
  - stop_name (human readable)
  - departures (list of upcoming departures; flattened key structure for easy templating)
  - infotexts (service announcements/disruptions, original structure preserved)
- Configurable time window via Options Flow:
  - minutes_before (default 0)
  - minutes_after (default 60)
- Automatic updates approximately every 30 seconds (cloud polling)
- Works entirely via the UI (Config Flow and Options Flow)

## Requirements

- Golemio (PID) API key
  - Request one at: https://api.golemio.cz/api-keys/dashboard
- PID stop IDs you want to monitor
  - You can obtain stop IDs from:
    - PID datasets: https://opendata.praha.eu/datasets/https%3A%2F%2Fapi.opendata.praha.eu%2Flod%2Fcatalog%2F9a6a1d8e-45b9-41de-b9ae-0bcec7126876
    - Golemio API docs: https://api.golemio.cz/pid/docs/openapi/#/
  - Use the identifier that corresponds to a PID stop (see the datasets/docs)

## Installation

Option A — HACS (Custom repository)
1. In HACS → Integrations, open the menu (⋮) → Custom repositories.
2. Add repository URL: `https://github.com/martin-sladecek/pid-departure-board` with Category: Integration.
3. Install “PID Departure Boards” and restart Home Assistant.
4. Go to Settings → Devices & Services → Add Integration → search for “PID Departure Boards”.

Option B — Manual
1. Copy this repository directory into your Home Assistant config at:
   `<config>/custom_components/pid_departure_board`
2. Restart Home Assistant.
3. Go to Settings → Devices & Services → Add Integration → search for “PID Departure Boards”.

## Configuration

When adding the integration via the UI, you will be prompted for:
- API key (your Golemio key)
- Stop IDs (multiple values supported)
  - You can paste a comma-separated list, or enter multiple values when prompted.

After the integration is created, you can adjust options from the integration’s Configure page:
- stop_ids: Update the set of monitored stops
- minutes_before: Integer, default 0
- minutes_after: Integer, default 60

Validation rules:
- minutes_before: must be between -4320 and 30 (minutes)
- minutes_after: must be between -4350 and 4320 (minutes)
- The sum (minutes_before + minutes_after) must be > 0

Entity naming:
- One sensor per stop ID
- Unique ID: `<stop_id>_departures`
- Name: `<Stop Name> Departures`

## Entity Model

State (native_value):
- Next predicted departure time for the stop (ISO timestamp displayed as time in HA)
- If no upcoming departures are available, the sensor state is unknown

Attributes:
- stop_name: Human-readable name from API
- departures: List of departures; each departure is a flattened dictionary (nested fields are converted into keys joined by “_”)
- infotexts: List of service messages related to the stop; original nested structure is preserved

Notes:
- departures are intentionally flattened for simpler templates and dashboards
- infotexts remain nested to preserve structure such as multilingual content and validity ranges

## Update Interval

- The integration polls the API approximately every 30 seconds (hard-coded in the coordinator).

## Disclaimer

This project is not affiliated with PID or Golemio. Use of the API is subject to Golemio’s terms and rate limits.
