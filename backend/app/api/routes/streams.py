from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.streams import AddOfferRequest, StreamsEditorResponse
from app.services.keitaro import (
    KeitaroAPIError,
    KeitaroClient,
    KeitaroNotConfiguredError,
    get_keitaro_client,
)
from app.services.streams import (
    StreamServiceError,
    add_offer,
    bring_back_offer,
    cancel_stream_edits,
    fetch_streams,
    get_streams_editor,
    push_stream,
    remove_offer,
    set_offer_pin,
)

router = APIRouter(prefix="/campaigns/{campaign_id}/streams")


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, StreamServiceError):
        code = status.HTTP_400_BAD_REQUEST
        if "not found" in str(exc).lower():
            code = status.HTTP_404_NOT_FOUND
        return HTTPException(status_code=code, detail=str(exc))
    if isinstance(exc, KeitaroNotConfiguredError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    if isinstance(exc, KeitaroAPIError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": str(exc),
                "keitaro_status": exc.status_code,
                "keitaro_payload": exc.payload,
            },
        )
    raise exc


@router.get("", response_model=StreamsEditorResponse)
def read_streams(
    campaign_id: str,
    db: Session = Depends(get_db),
) -> StreamsEditorResponse:
    try:
        return get_streams_editor(db, campaign_id)
    except StreamServiceError as exc:
        raise _http_error(exc) from exc


@router.post("/fetch", response_model=StreamsEditorResponse)
def fetch_from_keitaro(
    campaign_id: str,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro_client),
) -> StreamsEditorResponse:
    try:
        return fetch_streams(db=db, client=client, campaign_id=campaign_id)
    except (StreamServiceError, KeitaroNotConfiguredError, KeitaroAPIError) as exc:
        raise _http_error(exc) from exc


@router.post("/{stream_id}/offers", response_model=StreamsEditorResponse)
def add_stream_offer(
    campaign_id: str,
    stream_id: int,
    body: AddOfferRequest,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro_client),
) -> StreamsEditorResponse:
    try:
        return add_offer(
            db=db,
            client=client,
            campaign_id=campaign_id,
            keitaro_stream_id=stream_id,
            offer_id=body.offer_id,
        )
    except (StreamServiceError, KeitaroNotConfiguredError, KeitaroAPIError) as exc:
        raise _http_error(exc) from exc


@router.post("/{stream_id}/offers/{offer_id}/remove", response_model=StreamsEditorResponse)
def remove_stream_offer(
    campaign_id: str,
    stream_id: int,
    offer_id: int,
    db: Session = Depends(get_db),
) -> StreamsEditorResponse:
    try:
        return remove_offer(
            db=db,
            campaign_id=campaign_id,
            keitaro_stream_id=stream_id,
            offer_id=offer_id,
        )
    except StreamServiceError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/{stream_id}/offers/{offer_id}/bring-back",
    response_model=StreamsEditorResponse,
)
def bring_back_stream_offer(
    campaign_id: str,
    stream_id: int,
    offer_id: int,
    db: Session = Depends(get_db),
) -> StreamsEditorResponse:
    try:
        return bring_back_offer(
            db=db,
            campaign_id=campaign_id,
            keitaro_stream_id=stream_id,
            offer_id=offer_id,
        )
    except StreamServiceError as exc:
        raise _http_error(exc) from exc


@router.post("/{stream_id}/offers/{offer_id}/pin", response_model=StreamsEditorResponse)
def pin_stream_offer(
    campaign_id: str,
    stream_id: int,
    offer_id: int,
    db: Session = Depends(get_db),
) -> StreamsEditorResponse:
    try:
        return set_offer_pin(
            db=db,
            campaign_id=campaign_id,
            keitaro_stream_id=stream_id,
            offer_id=offer_id,
            pinned=True,
        )
    except StreamServiceError as exc:
        raise _http_error(exc) from exc


@router.post("/{stream_id}/offers/{offer_id}/unpin", response_model=StreamsEditorResponse)
def unpin_stream_offer(
    campaign_id: str,
    stream_id: int,
    offer_id: int,
    db: Session = Depends(get_db),
) -> StreamsEditorResponse:
    try:
        return set_offer_pin(
            db=db,
            campaign_id=campaign_id,
            keitaro_stream_id=stream_id,
            offer_id=offer_id,
            pinned=False,
        )
    except StreamServiceError as exc:
        raise _http_error(exc) from exc


@router.post("/{stream_id}/push", response_model=StreamsEditorResponse)
def push_to_keitaro(
    campaign_id: str,
    stream_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro_client),
) -> StreamsEditorResponse:
    try:
        return push_stream(
            db=db,
            client=client,
            campaign_id=campaign_id,
            keitaro_stream_id=stream_id,
        )
    except (StreamServiceError, KeitaroNotConfiguredError, KeitaroAPIError) as exc:
        raise _http_error(exc) from exc


@router.post("/{stream_id}/cancel", response_model=StreamsEditorResponse)
def cancel_edits(
    campaign_id: str,
    stream_id: int,
    db: Session = Depends(get_db),
) -> StreamsEditorResponse:
    try:
        return cancel_stream_edits(
            db=db,
            campaign_id=campaign_id,
            keitaro_stream_id=stream_id,
        )
    except StreamServiceError as exc:
        raise _http_error(exc) from exc
