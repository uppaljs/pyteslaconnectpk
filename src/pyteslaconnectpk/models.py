"""Data models for Tesla Connect Pakistan API responses.

Each model wraps a raw API response dict and exposes typed properties
that mirror the API fields exactly.  Command methods that mutate device
state use the stored Auth reference to issue requests and update the
raw data in place.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .auth import Auth


class Device:
    """A device returned in the sign-in device list."""

    def __init__(self, raw_data: dict[str, Any], auth: Auth) -> None:
        self.raw_data = raw_data
        self.auth = auth

    @property
    def device_id(self) -> str:
        """Return the unique device identifier."""
        return self.raw_data["device_id"]

    @property
    def name(self) -> str:
        """Return the human-readable device name."""
        return self.raw_data.get("name", "")

    @property
    def type_id(self) -> int:
        """Return the device type (1=inverter, 2=geyser)."""
        return self.raw_data.get("type_id", 0)

    @property
    def model_id(self) -> int:
        """Return the device model identifier."""
        return self.raw_data.get("model_id", 0)

    @property
    def image(self) -> str:
        """Return the device image path."""
        return self.raw_data.get("image", "")

    @property
    def online(self) -> bool:
        """Return True if the device is online."""
        return self.raw_data.get("online", False)

    @property
    def energy_day(self) -> int:
        """Return daily energy value."""
        return self.raw_data.get("energy_day", 0)

    @property
    def curr_temp(self) -> int:
        """Return the current temperature."""
        return self.raw_data.get("curr_temp", 0)

    @property
    def savings(self) -> int:
        """Return the savings value."""
        return self.raw_data.get("savings", 0)


class TimeSlot:
    """A single hourly timer slot."""

    def __init__(self, raw_data: dict[str, Any]) -> None:
        self.raw_data = raw_data

    @property
    def time(self) -> str:
        """Return the time range label (e.g. '4:00 - 4:59')."""
        return self.raw_data.get("time", "")

    @property
    def status(self) -> bool:
        """Return True if this slot is enabled."""
        return self.raw_data.get("status", False)


class GeyserDetails:
    """Detailed state of a geyser device."""

    def __init__(self, raw_data: dict[str, Any], auth: Auth) -> None:
        self.raw_data = raw_data
        self.auth = auth

    @property
    def device_id(self) -> str:
        """Return the device identifier."""
        return self.raw_data.get("device_id", "")

    @property
    def curr_mode(self) -> int:
        """Return the current operating mode integer."""
        return self.raw_data.get("curr_mode", 0)

    @property
    def user_mode(self) -> int:
        """Return the user-selected mode integer."""
        return self.raw_data.get("user_mode", 0)

    @property
    def burner(self) -> int:
        """Return the burner state (1=on, 0=off)."""
        return self.raw_data.get("burner", 0)

    @property
    def boost(self) -> int:
        """Return the boost state (1=on, 0=off)."""
        return self.raw_data.get("boost", 0)

    @property
    def two_hour_mode(self) -> int:
        """Return the two-hour mode state (1=on, 0=off)."""
        return self.raw_data.get("two_hour_mode", 0)

    @property
    def vacation(self) -> int:
        """Return the vacation mode state (1=on, 0=off)."""
        return self.raw_data.get("vacation", 0)

    @property
    def solar(self) -> int:
        """Return the solar state (1=on, 0=off)."""
        return self.raw_data.get("solar", 0)

    @property
    def temp_limit(self) -> int:
        """Return the target temperature limit in degrees Celsius."""
        return self.raw_data.get("temp_limit", 0)

    @property
    def curr_temp(self) -> int:
        """Return the current water temperature in degrees Celsius."""
        return self.raw_data.get("curr_temp", 0)

    @property
    def gas_units(self) -> int:
        """Return cumulative gas consumption in cubic metres."""
        return self.raw_data.get("gas_units", 0)

    @property
    def electric_units(self) -> int:
        """Return cumulative electric consumption in watt-hours."""
        return self.raw_data.get("electric_units", 0)

    @property
    def status_label(self) -> str:
        """Return the human-readable status string."""
        return self.raw_data.get("status_label", "")

    @property
    def temp_label(self) -> str:
        """Return the human-readable temperature label."""
        return self.raw_data.get("temp_label", "")

    @property
    def times(self) -> list[TimeSlot]:
        """Return the 24-hour timer schedule as TimeSlot objects."""
        return [TimeSlot(t) for t in self.raw_data.get("times", [])]

    # -- Commands --

    async def set_boost(self, enabled: bool) -> None:
        """Enable or disable boost mode."""
        await self.auth.ensure_token()
        data = await self.auth.request(
            "post",
            "geyser-boost",
            json={"boost": 1 if enabled else 0, "device_id": self.device_id},
        )
        self.raw_data.update(data)

    async def set_mode(self, curr_mode: int, user_mode: int) -> None:
        """Set the operating mode."""
        await self.auth.ensure_token()
        data = await self.auth.request(
            "post",
            "geyser-mode",
            json={
                "curr_mode": curr_mode,
                "device_id": self.device_id,
                "user_mode": user_mode,
            },
        )
        self.raw_data.update(data)

    async def set_temp_limit(self, temp_limit: int) -> None:
        """Set the target temperature limit."""
        await self.auth.ensure_token()
        data = await self.auth.request(
            "post",
            "geyser-temp-limit",
            json={"device_id": self.device_id, "temp_limit": temp_limit},
        )
        self.raw_data.update(data)

    async def set_timer(self, times: list[dict[str, Any]]) -> None:
        """Set the hourly timer schedule."""
        await self.auth.ensure_token()
        data = await self.auth.request(
            "post",
            "geyser-time",
            json={"device_id": self.device_id, "times": times},
        )
        self.raw_data.update(data)

    async def set_two_hour_mode(self, enabled: bool) -> None:
        """Enable or disable two-hour mode."""
        await self.auth.ensure_token()
        data = await self.auth.request(
            "post",
            "geyser-two-hour-mode",
            json={"device_id": self.device_id, "two_hour_mode": 1 if enabled else 0},
        )
        self.raw_data.update(data)

    async def set_vacation_mode(self, enabled: bool) -> None:
        """Enable or disable vacation mode."""
        await self.auth.ensure_token()
        data = await self.auth.request(
            "post",
            "geyser-vacation-mode",
            json={"device_id": self.device_id, "vacation": 1 if enabled else 0},
        )
        self.raw_data.update(data)


class InverterDetails:
    """Detailed state of an inverter device."""

    def __init__(self, raw_data: dict[str, Any], auth: Auth) -> None:
        self.raw_data = raw_data
        self.auth = auth

    @property
    def device_id(self) -> str:
        """Return the device identifier."""
        return self.raw_data.get("device_id", "")

    @property
    def battery_percentage(self) -> int:
        """Return the battery charge percentage."""
        return self.raw_data.get("battery_percentage", 0)

    @property
    def battery_voltage(self) -> int:
        """Return the battery voltage."""
        return self.raw_data.get("battery_voltage", 0)

    @property
    def energy_day(self) -> int:
        """Return daily energy in watt-hours."""
        return self.raw_data.get("energy_day", 0)

    @property
    def energy_week(self) -> int:
        """Return weekly energy in watt-hours."""
        return self.raw_data.get("energy_week", 0)

    @property
    def energy_month(self) -> int:
        """Return monthly energy in watt-hours."""
        return self.raw_data.get("energy_month", 0)

    @property
    def energy_total(self) -> int:
        """Return lifetime energy in watt-hours."""
        return self.raw_data.get("energy_total", 0)

    @property
    def energy_year(self) -> int:
        """Return yearly energy in watt-hours."""
        return self.raw_data.get("energy_year", 0)

    @property
    def savings_day(self) -> int:
        """Return daily savings value."""
        return self.raw_data.get("savings_day", 0)

    @property
    def savings_week(self) -> int:
        """Return weekly savings value."""
        return self.raw_data.get("savings_week", 0)

    @property
    def faults(self) -> int:
        """Return the current fault code."""
        return self.raw_data.get("faults", 0)

    @property
    def grid_status(self) -> int:
        """Return grid power status (1=available, 0=unavailable)."""
        return self.raw_data.get("grid_status", 0)

    @property
    def solar_status(self) -> int:
        """Return solar power status (1=generating, 0=inactive)."""
        return self.raw_data.get("solar_status", 0)

    @property
    def battery_direction(self) -> int:
        """Return battery charge direction."""
        return self.raw_data.get("battery_direction", 0)
