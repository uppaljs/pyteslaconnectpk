"""Tests for the pyteslaconnectpk library."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from pyteslaconnectpk import (
    API_AUTH_KEY,
    TOKEN_MAX_AGE,
    Auth,
    Device,
    GeyserDetails,
    InverterDetails,
    TeslaConnectApi,
    TeslaConnectApiError,
    TeslaConnectAuthError,
    TimeSlot,
)
from pyteslaconnectpk.const import OKHTTP_UA

MOCK_PHONE = "03001234567"
MOCK_PASSWORD = "testpass"
MOCK_SIGN_IN_RESPONSE = {
    "devices": [
        {"device_id": "g1", "name": "Geyser", "type_id": 2, "online": True, "curr_temp": 45},
        {"device_id": "i1", "name": "Inverter", "type_id": 1, "online": True},
    ],
    "name": "Test User",
    "phone": "3001234567",
    "status": "Success",
    "token": "dGVzdHRva2Vu",
}
MOCK_GEYSER_DETAILS = {
    "boost": 0,
    "burner": 1,
    "curr_mode": 0,
    "curr_temp": 46,
    "device_id": "g1",
    "electric_units": 3828000,
    "gas_units": 4661,
    "status": "Success",
    "status_label": "Currently Using Gas",
    "temp_label": "Heating up to 50 degrees",
    "temp_limit": 50,
    "times": [{"status": False, "time": "0:00 - 0:59"}, {"status": True, "time": "1:00 - 1:59"}],
    "two_hour_mode": 0,
    "user_mode": 2,
    "vacation": 0,
}
MOCK_INVERTER_DETAILS = {
    "battery_percentage": 85,
    "battery_voltage": 52,
    "device_id": "i1",
    "energy_day": 1500,
    "faults": 0,
    "grid_status": 1,
    "solar_status": 1,
    "status": "Success",
}


# ------------------------------------------------------------------
# Auth tests
# ------------------------------------------------------------------


class TestAuth:
    """Tests for the Auth layer."""

    def test_user_agent(self) -> None:
        """Session should use OkHttp user agent."""
        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        assert auth._session.headers["User-Agent"] == OKHTTP_UA

    def test_no_token_initially(self) -> None:
        """A fresh auth instance should have no token."""
        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        assert auth.token is None
        assert auth.token_expired is True

    def test_token_expired_when_stale(self) -> None:
        """Token should expire after TOKEN_MAX_AGE seconds."""
        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        auth._token = "tok"
        auth._token_ts = time.time() - TOKEN_MAX_AGE - 1
        assert auth.token_expired is True

    def test_token_valid_when_fresh(self) -> None:
        """Token should be valid when recently acquired."""
        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        auth._token = "tok"
        auth._token_ts = time.time()
        assert auth.token_expired is False

    def test_custom_host(self) -> None:
        """Custom host should be stored with trailing slash."""
        auth = Auth(host="http://local", phone=MOCK_PHONE, password=MOCK_PASSWORD)
        assert auth._host == "http://local/"

    def test_injected_session(self) -> None:
        """An injected session should be used instead of creating one."""
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD, session=session)
        assert auth._session is session

    @patch("pyteslaconnectpk.auth.requests.Session")
    def test_key_header(self, mock_cls: MagicMock) -> None:
        """Key header should be timestamp + API_AUTH_KEY."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "Success"}
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.request.return_value = mock_resp
        session.headers = {}

        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        auth._session = session
        auth.request("post", "test", json={})

        key = session.request.call_args.kwargs["headers"]["key"]
        assert key.endswith(API_AUTH_KEY)
        assert key[: -len(API_AUTH_KEY)].isdigit()

    @patch("pyteslaconnectpk.auth.requests.Session")
    def test_compact_json(self, mock_cls: MagicMock) -> None:
        """Body should use compact JSON encoding."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "Success"}
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.request.return_value = mock_resp
        session.headers = {}

        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        auth._session = session
        auth.request("post", "test", json={"a": 1, "b": 2})

        body = session.request.call_args.kwargs["data"]
        assert " " not in body

    @patch("pyteslaconnectpk.auth.requests.Session")
    def test_connection_error(self, mock_cls: MagicMock) -> None:
        """Connection errors should raise TeslaConnectApiError."""
        session = mock_cls.return_value
        session.request.side_effect = requests.exceptions.ConnectionError("refused")
        session.headers = {}

        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        auth._session = session
        with pytest.raises(TeslaConnectApiError, match="Connection error"):
            auth.request("post", "test")

    @patch("pyteslaconnectpk.auth.requests.Session")
    def test_timeout(self, mock_cls: MagicMock) -> None:
        """Timeouts should raise TeslaConnectApiError."""
        session = mock_cls.return_value
        session.request.side_effect = requests.exceptions.Timeout("timed out")
        session.headers = {}

        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        auth._session = session
        with pytest.raises(TeslaConnectApiError, match="timed out"):
            auth.request("post", "test")

    @patch("pyteslaconnectpk.auth.requests.Session")
    def test_sign_in_success(self, mock_cls: MagicMock) -> None:
        """Successful sign-in should cache the token."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SIGN_IN_RESPONSE
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.request.return_value = mock_resp
        session.headers = {}

        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        auth._session = session
        data = auth.sign_in()

        assert data["status"] == "Success"
        assert auth.token == MOCK_SIGN_IN_RESPONSE["token"]

    @patch("pyteslaconnectpk.auth.requests.Session")
    def test_sign_in_failure(self, mock_cls: MagicMock) -> None:
        """Failed sign-in should raise TeslaConnectAuthError."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": "Bad creds", "status": "Failure"}
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.request.return_value = mock_resp
        session.headers = {}

        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        auth._session = session
        with pytest.raises(TeslaConnectAuthError, match="Bad creds"):
            auth.sign_in()

    def test_close(self) -> None:
        """close() should close the underlying session."""
        auth = Auth(phone=MOCK_PHONE, password=MOCK_PASSWORD)
        auth._session = MagicMock()
        auth.close()
        auth._session.close.assert_called_once()


# ------------------------------------------------------------------
# Data model tests
# ------------------------------------------------------------------


class TestDevice:
    """Tests for the Device model."""

    def test_properties(self) -> None:
        """Device properties should map to raw_data keys."""
        raw = MOCK_SIGN_IN_RESPONSE["devices"][0]
        dev = Device(raw, MagicMock())
        assert dev.device_id == "g1"
        assert dev.name == "Geyser"
        assert dev.type_id == 2
        assert dev.online is True
        assert dev.curr_temp == 45


class TestGeyserDetails:
    """Tests for the GeyserDetails model."""

    def test_properties(self) -> None:
        """GeyserDetails properties should map to raw_data keys."""
        geyser = GeyserDetails(MOCK_GEYSER_DETAILS, MagicMock())
        assert geyser.device_id == "g1"
        assert geyser.curr_temp == 46
        assert geyser.temp_limit == 50
        assert geyser.curr_mode == 0
        assert geyser.user_mode == 2
        assert geyser.burner == 1
        assert geyser.boost == 0
        assert geyser.gas_units == 4661
        assert geyser.electric_units == 3828000
        assert geyser.status_label == "Currently Using Gas"

    def test_times(self) -> None:
        """Times should be parsed as TimeSlot objects."""
        geyser = GeyserDetails(MOCK_GEYSER_DETAILS, MagicMock())
        times = geyser.times
        assert len(times) == 2
        assert isinstance(times[0], TimeSlot)
        assert times[0].status is False
        assert times[1].status is True


class TestInverterDetails:
    """Tests for the InverterDetails model."""

    def test_properties(self) -> None:
        """InverterDetails properties should map to raw_data keys."""
        inv = InverterDetails(MOCK_INVERTER_DETAILS, MagicMock())
        assert inv.device_id == "i1"
        assert inv.battery_percentage == 85
        assert inv.battery_voltage == 52
        assert inv.energy_day == 1500
        assert inv.faults == 0
        assert inv.grid_status == 1
        assert inv.solar_status == 1


# ------------------------------------------------------------------
# TeslaConnectApi (root class) tests
# ------------------------------------------------------------------


class TestTeslaConnectApi:
    """Tests for the high-level API client."""

    @patch("pyteslaconnectpk.auth.requests.Session")
    def test_sign_in_populates_devices(self, mock_cls: MagicMock) -> None:
        """sign_in should populate typed Device objects."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SIGN_IN_RESPONSE
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.request.return_value = mock_resp
        session.headers = {}

        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api.auth._session = session
        api.sign_in()

        assert api.user_name == "Test User"
        assert len(api.devices) == 2
        assert isinstance(api.devices[0], Device)
        assert api.devices[0].name == "Geyser"

    @patch("pyteslaconnectpk.auth.requests.Session")
    def test_get_geyser_details_returns_model(self, mock_cls: MagicMock) -> None:
        """get_geyser_details should return a GeyserDetails model."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_GEYSER_DETAILS
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.request.return_value = mock_resp
        session.headers = {}

        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api.auth._session = session
        api.auth._token = "tok"
        api.auth._token_ts = time.time()

        details = api.get_geyser_details("g1")
        assert isinstance(details, GeyserDetails)
        assert details.curr_temp == 46

    @patch("pyteslaconnectpk.auth.requests.Session")
    def test_get_inverter_details_returns_model(self, mock_cls: MagicMock) -> None:
        """get_inverter_details should return an InverterDetails model."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_INVERTER_DETAILS
        mock_resp.raise_for_status.return_value = None
        session = mock_cls.return_value
        session.request.return_value = mock_resp
        session.headers = {}

        api = TeslaConnectApi(MOCK_PHONE, MOCK_PASSWORD)
        api.auth._session = session
        api.auth._token = "tok"
        api.auth._token_ts = time.time()

        details = api.get_inverter_details("i1")
        assert isinstance(details, InverterDetails)
        assert details.battery_percentage == 85
