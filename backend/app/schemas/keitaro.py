from pydantic import BaseModel, Field


class KeitaroStatusResponse(BaseModel):
    configured: bool
    reachable: bool | None = Field(
        default=None,
        description="None if not configured; True/False after ping attempt",
    )
    keitaro_url: str | None = None
    error: str | None = None
