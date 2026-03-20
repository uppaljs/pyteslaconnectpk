"""Authentication layer for the Tesla Connect Pakistan API.

Responsible for making authenticated HTTP requests.  Unaware of the
specific resources or data being requested — that responsibility
belongs to the data model and API root classes.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

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
        session: Optional pre-configured requests.Session.
        timeout: HTTP request timeout in seconds.

    """

    def __init__(
        self,
        host: str = BASE_URL,
        phone: str = "",
        password: str = "",
        *,
        session: requests.Session | None = None,
        timeout: int = 30,
    ) -> None:
        self._host = host.rstrip("/") + "/"
        self._phone = phone
        self._password = password
        self._timeout = timeout
        self._token: str | None = None
        self._token_ts: float = 0.0
        self._session = session or self._create_session()

    @staticmethod
    def _create_session() -> requests.Session:
        """Create a session with OkHttp-compatible default headers."""
        session = requests.Session()
        session.headers.update(
            {
                "Accept-Encoding": "gzip",
                "Connection": "keep-alive",
                "User-Agent": OKHTTP_UA,
            }
        )
        return session

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

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make an authenticated request to the API.

        The ``key`` header (timestamp + API key) is added automatically.
        If a token is available, it is injected into the JSON body.

        Args:
            method: HTTP method (currently always "post" for this API).
            path: Endpoint path relative to the host.
            **kwargs: Passed through to requests; ``json`` is the body dict.

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
            "key": ts + API_AUTH_KEY,
        }

        try:
            resp = self._session.request(
                method,
                url,
                data=body,
                headers=headers,
                timeout=self._timeout,
            )
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise TeslaConnectApiError(f"Connection error: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            raise TeslaConnectApiError(f"Request timed out: {exc}") from exc
        except requests.exceptions.HTTPError as exc:
            raise TeslaConnectApiError(f"HTTP {resp.status_code}") from exc

        data: dict[str, Any] = resp.json()
        _LOGGER.debug("POST %s status=%s", path, data.get("status", "?"))
        return data

    def sign_in(self) -> dict[str, Any]:
        """Authenticate and cache the session token.

        Returns:
            The full sign-in response dict (status, name, phone, token, devices).

        Raises:
            TeslaConnectAuthError: When the API returns a non-success status.

        """
        data = self.request(
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

    def ensure_token(self) -> None:
        """Re-authenticate if the cached token is missing or stale."""
        if self.token_expired:
            self.sign_in()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()
