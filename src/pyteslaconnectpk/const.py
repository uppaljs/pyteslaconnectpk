"""Constants for the Tesla Connect Pakistan API client."""

from __future__ import annotations

# API connection.
API_AUTH_KEY: str = "146ngU0W4Hx0aahiyYShehO7ARo5XPhCJcT"
BASE_URL: str = "https://api.tesla-tech.com/"
OKHTTP_UA: str = "okhttp/4.12.0"

# Device types (from the DeviceType enum in the Android app).
DEVICE_TYPE_GEYSER: int = 2
DEVICE_TYPE_INVERTER: int = 1

# Geyser operation modes (from the GeyserMode enum in the Android app).
GEYSER_MODE_AUTOMATIC: int = 2
GEYSER_MODE_ELECTRICITY: int = 1
GEYSER_MODE_GAS: int = 0
GEYSER_MODE_SOLAR_DISABLED: int = 4
GEYSER_MODE_SOLAR_ENABLED: int = 3

# Device status values (from the Status enum in the Android app).
STATUS_OFF: int = 0
STATUS_ON: int = 1

# Seconds before a cached token is considered stale and a re-login is forced.
TOKEN_MAX_AGE: int = 55 * 60
