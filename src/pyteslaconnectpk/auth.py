"""Authentication layer for the Tesla Connect Pakistan API.

Responsible for making authenticated HTTP requests.  Unaware of the
specific resources or data being requested — that responsibility
belongs to the data model and API root classes.

Uses ``aiohttp`` for async HTTP.  The caller can inject a shared
``ClientSession`` (recommended for Home Assistant) or let the class
create its own.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import aiohttp

from .const import API_AUTH_KEY, BASE_URL, OKHTTP_UA, TOKEN_MAX_AGE
from .exceptions import TeslaConnectApiError, TeslaConnectAuthError

_LOGGER = logging.getLogger(__name__)


class Auth:
    """Make authenticated requests to the Tesla Connect API.

    Mimics the HTTP fingerprint of the official Android app (OkHttp
    User-Agent, compact JSON, timestamp-based auth header).

    Args:
        host: API base URL.
        phone: Account phone number.
        password: Account password.
        websession: Optional pre-configured aiohttp.ClientSession.
            When provided, the caller owns the session lifecycle.
        timeout: HTTP request timeout in seconds.

    """

    def __init__(
        self,
        host: str = BASE_URL,
        phone: str = "",
        password: str = "",
        *,
        websession: aiohttp.ClientSession | None = None,
        timeout: int = 30,
    ) -> None:
        self._host = host.rstrip("/") + "/"
        self._phone = phone
        self._password = password
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._token: str | None = None
        self._token_ts: float = 0.0
        self._websession = websession
        self._owns_session = websession is None

    @property
    def token(self) -> str | None:
        """Return the current access token."""
        return self._token

    @property
    def token_expired(self) -> bool:
        """Return True when the cached token is absent or stale."""
        if not self._token:
            return True
        return (time.time() - self._token_ts) > TOKEN_MAX_AGE

    def _get_session(self) -> aiohttp.ClientSession:
        """Return the active session, creating one if needed."""
        if self._websession is None or self._websession.closed:
            self._websession = aiohttp.ClientSession(
                headers={
                    "Accept-Encoding": "gzip",
                    "Connection": "keep-alive",
                    "User-Agent": OKHTTP_UA,
                },
                timeout=self._timeout,
            )
            self._owns_session = True
        return self._websession

    async def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make an authenticated request to the API.

        Args:
            method: HTTP method (currently always "post" for this API).
            path: Endpoint path relative to the host.
            **kwargs: ``json`` is the body dict.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            TeslaConnectApiError: On connection failure, timeout, or HTTP error.

        """
        url = f"{self._host}{path}"
        ts = str(int(time.time()))

        payload = kwargs.pop("json", {}) or {}
        if self._token and "token" not in payload:
            payload["token"] = self._token

        body = json.dumps(payload, separators=(",", ":"))

        headers = {
            "Content-Length": str(len(body.encode())),
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": OKHTTP_UA,
            "key": ts + API_AUTH_KEY,
        }

        session = self._get_session()
        try:
            async with session.request(
                method,
                url,
                data=body,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                data: dict[str, Any] = await resp.json(content_type=None)
        except aiohttp.ClientConnectionError as exc:
            raise TeslaConnectApiError(f"Connection error: {exc}") from exc
        except TimeoutError as exc:
            raise TeslaConnectApiError(f"Request timed out: {exc}") from exc
        except aiohttp.ClientResponseError as exc:
            raise TeslaConnectApiError(f"HTTP {exc.status}") from exc

        _LOGGER.debug("POST %s status=%s", path, data.get("status", "?"))
        return data

    async def sign_in(self) -> dict[str, Any]:
        """Authenticate and cache the session token.

        Returns:
            The full sign-in response dict.

        Raises:
            TeslaConnectAuthError: When the API returns a non-success status.

        """
        data = await self.request(
            "post",
            "sign-in",
            json={
                "firebase_token": "",
                "password": self._password,
                "phone": self._phone,
            },
        )
        if data.get("status") != "Success":
            raise TeslaConnectAuthError(data.get("message", "Login failed"))
        self._token = data["token"]
        self._token_ts = time.time()
        _LOGGER.info("Signed in as %s", data.get("name"))
        return data

    async def ensure_token(self) -> None:
        """Re-authenticate if the cached token is missing or stale."""
        if self.token_expired:
            await self.sign_in()

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._websession and not self._websession.closed:
            await self._websession.close()
