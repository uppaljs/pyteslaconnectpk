"""High-level API client for Tesla Connect Pakistan.

This is the main entry point for library consumers.  It composes the
Auth layer (handles HTTP + token lifecycle) with typed data models
(Device, GeyserDetails, InverterDetails).
"""

from __future__ import annotations

from typing import Any

import requests

from .auth import Auth
from .const import BASE_URL
from .models import Device, GeyserDetails, InverterDetails


class TeslaConnectApi:
    """High-level client for the Tesla Connect Pakistan API.

    Wraps Auth for authentication and returns typed model objects
    instead of raw dicts.  The ``raw_data`` dict is always accessible
    on each model for integration code that needs it.

    Args:
        phone: Account phone number.
        password: Account password.
        host: Override the default API base URL.
        session: Optional pre-configured requests.Session.
        timeout: HTTP request timeout in seconds.

    """

    def __init__(
        self,
        phone: str,
        password: str,
        *,
        host: str = BASE_URL,
        session: requests.Session | None = None,
        timeout: int = 30,
    ) -> None:
        self.auth = Auth(
            host=host,
            phone=phone,
            password=password,
            session=session,
            timeout=timeout,
        )
        self.devices: list[Device] = []
        self.user_name: str | None = None
        self.phone: str | None = None

    # ------------------------------------------------------------------
    # Convenience properties that delegate to auth
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

    def sign_in(self) -> dict[str, Any]:
        """Authenticate and populate the device list.

        Returns:
            The raw sign-in API response.

        """
        data = self.auth.sign_in()
        self.user_name = data.get("name")
        self.phone = data.get("phone")
        self.devices = [Device(d, self.auth) for d in data.get("devices", [])]
        return data

    def change_password(self, new_password: str) -> dict[str, Any]:
        """Change the account password."""
        self.auth.ensure_token()
        return self.auth.request(
            "post",
            "change-password",
            json={"password": new_password},
        )

    # ------------------------------------------------------------------
    # Device management
    # ------------------------------------------------------------------

    def refresh_devices(self) -> list[Device]:
        """Re-authenticate to obtain a fresh device list."""
        self.sign_in()
        return self.devices

    def add_device(self, device_id: str, name: str) -> dict[str, Any]:
        """Register a new device on the account."""
        self.auth.ensure_token()
        return self.auth.request(
            "post",
            "device-add",
            json={"device_id": device_id, "name": name},
        )

    def delete_device(self, device_id: str, name: str) -> dict[str, Any]:
        """Remove a device from the account."""
        self.auth.ensure_token()
        return self.auth.request(
            "post",
            "device-delete",
            json={"device_id": device_id, "name": name},
        )

    # ------------------------------------------------------------------
    # Geyser
    # ------------------------------------------------------------------

    def get_geyser_details(self, device_id: str, name: str = "") -> GeyserDetails:
        """Fetch the current state of a geyser device.

        Returns:
            A GeyserDetails model with typed property access.

        """
        self.auth.ensure_token()
        data = self.auth.request(
            "post",
            "geyser-details",
            json={"device_id": device_id, "name": name},
        )
        return GeyserDetails(data, self.auth)

    def set_geyser_boost(self, device_id: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable boost mode on a geyser."""
        self.auth.ensure_token()
        return self.auth.request(
            "post",
            "geyser-boost",
            json={"boost": 1 if enabled else 0, "device_id": device_id},
        )

    def set_geyser_mode(self, device_id: str, curr_mode: int, user_mode: int) -> dict[str, Any]:
        """Set the operating mode on a geyser."""
        self.auth.ensure_token()
        return self.auth.request(
            "post",
            "geyser-mode",
            json={
                "curr_mode": curr_mode,
                "device_id": device_id,
                "user_mode": user_mode,
            },
        )

    def set_geyser_temp_limit(self, device_id: str, temp_limit: int) -> dict[str, Any]:
        """Set the upper temperature limit on a geyser."""
        self.auth.ensure_token()
        return self.auth.request(
            "post",
            "geyser-temp-limit",
            json={"device_id": device_id, "temp_limit": temp_limit},
        )

    def set_geyser_timer(self, device_id: str, times: list[dict[str, Any]]) -> dict[str, Any]:
        """Configure scheduled timer slots on a geyser."""
        self.auth.ensure_token()
        return self.auth.request(
            "post",
            "geyser-time",
            json={"device_id": device_id, "times": times},
        )

    def set_geyser_two_hour_mode(self, device_id: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable two-hour heating mode on a geyser."""
        self.auth.ensure_token()
        return self.auth.request(
            "post",
            "geyser-two-hour-mode",
            json={"device_id": device_id, "two_hour_mode": 1 if enabled else 0},
        )

    def set_geyser_vacation_mode(self, device_id: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable vacation mode on a geyser."""
        self.auth.ensure_token()
        return self.auth.request(
            "post",
            "geyser-vacation-mode",
            json={"device_id": device_id, "vacation": 1 if enabled else 0},
        )

    # ------------------------------------------------------------------
    # Inverter
    # ------------------------------------------------------------------

    def get_inverter_details(self, device_id: str, name: str = "") -> InverterDetails:
        """Fetch the current state of an inverter device.

        Returns:
            An InverterDetails model with typed property access.

        """
        self.auth.ensure_token()
        data = self.auth.request(
            "post",
            "inverter-details",
            json={"device_id": device_id, "name": name},
        )
        return InverterDetails(data, self.auth)

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def get_strings(self) -> dict[str, Any]:
        """Fetch the localisation strings bundle from the API."""
        return self.auth.request("post", "strings.json")

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.auth.close()
