"""Errors raised by the Keitaro Admin API client."""


class KeitaroError(Exception):
    """Base error for Keitaro client failures."""


class KeitaroNotConfiguredError(KeitaroError):
    """KEITARO_URL or KEITARO_API_KEY is missing."""


class KeitaroAPIError(KeitaroError):
    """Non-success response from Keitaro Admin API."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: object | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
