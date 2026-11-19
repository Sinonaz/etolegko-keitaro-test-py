from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "keitaro-wrapper"
    debug: bool = False
    database_url: str = "sqlite:///./app.db"

    keitaro_url: str = ""
    keitaro_api_key: str = ""
    keitaro_domain_id: int | None = None
    keitaro_group_id: int | None = None
    keitaro_source_id: int | None = None
    # Used when IDs are empty: resolve by name (assignment defaults)
    keitaro_domain_name: str = ""
    keitaro_group_name: str = "FORTESTS"
    keitaro_source_name: str = "FORTESTS"
    keitaro_white_page_url: str = "https://google.com"

    @field_validator(
        "keitaro_domain_id",
        "keitaro_group_id",
        "keitaro_source_id",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
