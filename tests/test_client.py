"""Tests for the TeslaConnectApi client."""

from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from pyteslaconnectpk import (
    TeslaConnectApi,
    TeslaConnectApiError,
    TeslaConnectAuthError,
    TOKEN_MAX_AGE,
    API_AUTH_KEY,
)
from pyteslaconnectpk.const import OKHTTP_UA

MOCK_PHONE = "03001234567"
MOCK_PASSWORD = "testpass"
MOCK_SIGN_IN_RESPONSE = {
    "devices": [{"device_id": "g1", "name": "Geyser", "type_id": 2}],
    "name": "Test User",
    "phone": "3001234567",
    "status": "Success",
    "token": "dGVzdHRva2Vu",
}


class TestInit:
    """Tests for client initialisation."""

    def test_user_agent(self) -> None:
        """Session should use OkHttp user agent."""
        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        assert api._session.headers["User-Agent"] == OKHTTP_UA

    def test_no_token_initially(self) -> None:
        """A fresh client should have no token."""
        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        assert api.token is None
        assert api.token_expired is True

    def test_custom_base_url(self) -> None:
        """Custom base URL should be stored with trailing slash."""
        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD, base_url="http://local")
        assert api._base_url == "http://local/"

    def test_custom_timeout(self) -> None:
        """Custom timeout should be stored."""
        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD, timeout=10)
        assert api._timeout == 10


class TestTokenExpiry:
    """Tests for token lifecycle."""

    def test_expired_when_stale(self) -> None:
        """Token should expire after TOKEN_MAX_AGE seconds."""
        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api.token = "tok"
        api._token_ts = time.time() - TOKEN_MAX_AGE - 1
        assert api.token_expired is True

    def test_valid_when_fresh(self) -> None:
        """Token should be valid when recently acquired."""
        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api.token = "tok"
        api._token_ts = time.time()
        assert api.token_expired is False

    def test_ensure_token_calls_sign_in(self) -> None:
        """ensure_token should re-authenticate when expired."""
        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api.sign_in = MagicMock()
        api.ensure_token()
        api.sign_in.assert_called_once()

    def test_ensure_token_skips_when_valid(self) -> None:
        """ensure_token should skip when token is fresh."""
        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api.token = "tok"
        api._token_ts = time.time()
        api.sign_in = MagicMock()
        api.ensure_token()
        api.sign_in.assert_not_called()


class TestSignIn:
    """Tests for authentication."""

    @patch("pyteslaconnectpk.client.requests.Session")
    def test_success(self, mock_cls: MagicMock) -> None:
        """Successful sign-in should set token and devices."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SIGN_IN_RESPONSE
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.post.return_value = mock_resp
        session.headers = {}

        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api._session = session
        result = api.sign_in()

        assert result["status"] == "Success"
        assert api.token == MOCK_SIGN_IN_RESPONSE["token"]
        assert api.user_name == "Test User"
        assert len(api.devices) == 1

    @patch("pyteslaconnectpk.client.requests.Session")
    def test_failure_raises(self, mock_cls: MagicMock) -> None:
        """Failed sign-in should raise TeslaConnectAuthError."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": "Bad creds", "status": "Failure"}
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.post.return_value = mock_resp
        session.headers = {}

        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api._session = session

        with pytest.raises(TeslaConnectAuthError, match="Bad creds"):
            api.sign_in()


class TestPost:
    """Tests for the internal _post method."""

    @patch("pyteslaconnectpk.client.requests.Session")
    def test_connection_error(self, mock_cls: MagicMock) -> None:
        """Connection errors should raise TeslaConnectApiError."""
        session = mock_cls.return_value
        session.post.side_effect = requests.exceptions.ConnectionError("refused")
        session.headers = {}

        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api._session = session

        with pytest.raises(TeslaConnectApiError, match="Connection error"):
            api._post("test")

    @patch("pyteslaconnectpk.client.requests.Session")
    def test_timeout(self, mock_cls: MagicMock) -> None:
        """Timeouts should raise TeslaConnectApiError."""
        session = mock_cls.return_value
        session.post.side_effect = requests.exceptions.Timeout("timed out")
        session.headers = {}

        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api._session = session

        with pytest.raises(TeslaConnectApiError, match="timed out"):
            api._post("test")

    @patch("pyteslaconnectpk.client.requests.Session")
    def test_key_header(self, mock_cls: MagicMock) -> None:
        """Key header should be timestamp + API_AUTH_KEY."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "Success"}
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.post.return_value = mock_resp
        session.headers = {}

        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api._session = session
        api._post("test")

        key = session.post.call_args.kwargs["headers"]["key"]
        assert key.endswith(API_AUTH_KEY)
        assert key[: -len(API_AUTH_KEY)].isdigit()

    @patch("pyteslaconnectpk.client.requests.Session")
    def test_compact_json(self, mock_cls: MagicMock) -> None:
        """Body should use compact JSON encoding."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "Success"}
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.post.return_value = mock_resp
        session.headers = {}

        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api._session = session
        api._post("test", {"a": 1, "b": 2})

        body = session.post.call_args.kwargs["data"]
        assert " " not in body
        assert json.loads(body) == {"a": 1, "b": 2}


class TestClose:
    """Tests for session cleanup."""

    def test_close_calls_session_close(self) -> None:
        """close() should close the underlying session."""
        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api._session = MagicMock()
        api.close()
        api._session.close.assert_called_once()
