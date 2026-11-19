from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geo: str = Field(
        min_length=2,
        max_length=8,
        description="ISO country code, e.g. AU, MX, RO",
    )
    offer_id: int = Field(gt=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned

    @field_validator("geo")
    @classmethod
    def normalize_geo(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned.isalpha() or not (2 <= len(cleaned) <= 3):
            raise ValueError("geo must be a 2–3 letter country code")
        return cleaned


class CampaignResponse(BaseModel):
    id: str
    name: str
    geo: str
    offer_id: int
    keitaro_campaign_id: int
    keitaro_alias: str
    geo_stream_id: int | None = None
    offer_stream_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OfferSuggestion(BaseModel):
    id: int
    name: str
