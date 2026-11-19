"""Keitaro Admin API client (stub for later commits)."""

from app.core.config import Settings, get_settings


class KeitaroClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.keitaro_url.rstrip("/")
        self.api_key = self.settings.keitaro_api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)
