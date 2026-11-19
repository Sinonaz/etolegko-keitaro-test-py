from pydantic import BaseModel, Field


class StreamOfferView(BaseModel):
    offer_id: int
    offer_name: str
    share: int
    pinned: bool
    removed: bool


class StreamView(BaseModel):
    keitaro_stream_id: int
    name: str
    stream_type: str
    position: int
    schema: str
    filter_summary: str
    editable: bool
    dirty: bool
    offers: list[StreamOfferView]


class StreamsEditorResponse(BaseModel):
    campaign_id: str
    campaign_name: str
    keitaro_campaign_id: int
    keitaro_admin_url: str | None
    streams: list[StreamView]


class AddOfferRequest(BaseModel):
    offer_id: int = Field(gt=0)
