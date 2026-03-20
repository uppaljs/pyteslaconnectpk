"""Exception classes for the Tesla Connect Pakistan API client."""


class TeslaConnectApiError(Exception):
    """Raised when a non-authentication API call returns an error."""


class TeslaConnectAuthError(Exception):
    """Raised when authentication against the Tesla Connect API fails."""
