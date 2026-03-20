"""High-level async API client for Tesla Connect Pakistan.

This is the main entry point for library consumers.  It composes the
Auth layer (handles HTTP + token lifecycle) with typed data models
(Device, GeyserDetails, InverterDetails).
"""

from __future__ import annotations

from typing import Any

import aiohttp

from .auth import Auth
from .const import BASE_URL
from .models import Device, GeyserDetails, InverterDetails


class TeslaConnectApi:
    """High-level async client for the Tesla Connect Pakistan API.

    Wraps Auth for authentication and returns typed model objects
    instead of raw dicts.

    Args:
        phone: Account phone number.
        password: Account password.
        host: Override the default API base URL.
        websession: Optional aiohttp.ClientSession (injected by HA).
        timeout: HTTP request timeout in seconds.

    """

    def __init__(
        self,
        phone: str,
        password: str,
        *,
        host: str = BASE_URL,
        websession: aiohttp.ClientSession | None = None,
        timeout: int = 30,
    ) -> None:
        self.auth = Auth(
            host=host,
            phone=phone,
            password=password,
            websession=websession,
            timeout=timeout,
        )
        self.devices: list[Device] = []
        self.user_name: str | None = None
        self.phone: str | None = None

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def token(self) -> str | None:
        """Return the current session token."""
        return self.auth.token

    @property
    def token_expired(self) -> bool:
        """Return True when the cached token is absent or stale."""
        return self.auth.token_expired

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def sign_in(self) -> dict[str, Any]:
        """Authenticate and populate the device list."""
        data = await self.auth.sign_in()
        self.user_name = data.get("name")
        self.phone = data.get("phone")
        self.devices = [Device(d, self.auth) for d in data.get("devices", [])]
        return data

    async def change_password(self, new_password: str) -> dict[str, Any]:
        """Change the account password."""
        await self.auth.ensure_token()
        return await self.auth.request(
            "post",
            "change-password",
            json={"password": new_password},
        )

    # ------------------------------------------------------------------
    # Device management
    # ------------------------------------------------------------------

    async def refresh_devices(self) -> list[Device]:
        """Re-authenticate to obtain a fresh device list."""
        await self.sign_in()
        return self.devices

    async def add_device(self, device_id: str, name: str) -> dict[str, Any]:
        """Register a new device on the account."""
        await self.auth.ensure_token()
        return await self.auth.request(
            "post",
            "device-add",
            json={"device_id": device_id, "name": name},
        )

    async def delete_device(self, device_id: str, name: str) -> dict[str, Any]:
        """Remove a device from the account."""
        await self.auth.ensure_token()
        return await self.auth.request(
            "post",
            "device-delete",
            json={"device_id": device_id, "name": name},
        )

    # ------------------------------------------------------------------
    # Geyser
    # ------------------------------------------------------------------

    async def get_geyser_details(self, device_id: str, name: str = "") -> GeyserDetails:
        """Fetch the current state of a geyser device."""
        await self.auth.ensure_token()
        data = await self.auth.request(
            "post",
            "geyser-details",
            json={"device_id": device_id, "name": name},
        )
        return GeyserDetails(data, self.auth)

    async def set_geyser_boost(self, device_id: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable boost mode on a geyser."""
        await self.auth.ensure_token()
        return await self.auth.request(
            "post",
            "geyser-boost",
            json={"boost": 1 if enabled else 0, "device_id": device_id},
        )

    async def set_geyser_mode(
        self, device_id: str, curr_mode: int, user_mode: int
    ) -> dict[str, Any]:
        """Set the operating mode on a geyser."""
        await self.auth.ensure_token()
        return await self.auth.request(
            "post",
            "geyser-mode",
            json={
                "curr_mode": curr_mode,
                "device_id": device_id,
                "user_mode": user_mode,
            },
        )

    async def set_geyser_temp_limit(self, device_id: str, temp_limit: int) -> dict[str, Any]:
        """Set the upper temperature limit on a geyser."""
        await self.auth.ensure_token()
        return await self.auth.request(
            "post",
            "geyser-temp-limit",
            json={"device_id": device_id, "temp_limit": temp_limit},
        )

    async def set_geyser_timer(self, device_id: str, times: list[dict[str, Any]]) -> dict[str, Any]:
        """Configure scheduled timer slots on a geyser."""
        await self.auth.ensure_token()
        return await self.auth.request(
            "post",
            "geyser-time",
            json={"device_id": device_id, "times": times},
        )

    async def set_geyser_two_hour_mode(self, device_id: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable two-hour heating mode on a geyser."""
        await self.auth.ensure_token()
        return await self.auth.request(
            "post",
            "geyser-two-hour-mode",
            json={"device_id": device_id, "two_hour_mode": 1 if enabled else 0},
        )

    async def set_geyser_vacation_mode(self, device_id: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable vacation mode on a geyser."""
        await self.auth.ensure_token()
        return await self.auth.request(
            "post",
            "geyser-vacation-mode",
            json={"device_id": device_id, "vacation": 1 if enabled else 0},
        )

    # ------------------------------------------------------------------
    # Inverter
    # ------------------------------------------------------------------

    async def get_inverter_details(self, device_id: str, name: str = "") -> InverterDetails:
        """Fetch the current state of an inverter device."""
        await self.auth.ensure_token()
        data = await self.auth.request(
            "post",
            "inverter-details",
            json={"device_id": device_id, "name": name},
        )
        return InverterDetails(data, self.auth)

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    async def get_strings(self) -> dict[str, Any]:
        """Fetch the localisation strings bundle from the API."""
        return await self.auth.request("post", "strings.json")

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        await self.auth.close()
