"""Python API client for Tesla Connect Pakistan geyser and inverter devices."""

from .auth import Auth
from .client import TeslaConnectApi
from .const import (
    API_AUTH_KEY,
    BASE_URL,
    DEVICE_TYPE_GEYSER,
    DEVICE_TYPE_INVERTER,
    GEYSER_MODE_AUTOMATIC,
    GEYSER_MODE_ELECTRICITY,
    GEYSER_MODE_GAS,
    GEYSER_MODE_SOLAR_DISABLED,
    GEYSER_MODE_SOLAR_ENABLED,
    STATUS_OFF,
    STATUS_ON,
    TOKEN_MAX_AGE,
)
from .exceptions import TeslaConnectApiError, TeslaConnectAuthError
from .models import Device, GeyserDetails, InverterDetails, TimeSlot

__all__ = [
    "API_AUTH_KEY",
    "Auth",
    "BASE_URL",
    "DEVICE_TYPE_GEYSER",
    "DEVICE_TYPE_INVERTER",
    "Device",
    "GEYSER_MODE_AUTOMATIC",
    "GEYSER_MODE_ELECTRICITY",
    "GEYSER_MODE_GAS",
    "GEYSER_MODE_SOLAR_DISABLED",
    "GEYSER_MODE_SOLAR_ENABLED",
    "GeyserDetails",
    "InverterDetails",
    "STATUS_OFF",
    "STATUS_ON",
    "TOKEN_MAX_AGE",
    "TeslaConnectApi",
    "TeslaConnectApiError",
    "TeslaConnectAuthError",
    "TimeSlot",
]
