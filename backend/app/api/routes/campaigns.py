from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignCreateRequest, CampaignResponse
from app.services.campaigns import CampaignServiceError, create_campaign_with_streams
from app.services.keitaro import (
    KeitaroAPIError,
    KeitaroClient,
    KeitaroNotConfiguredError,
    get_keitaro_client,
)

router = APIRouter(prefix="/campaigns")


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    body: CampaignCreateRequest,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro_client),
) -> Campaign:
    try:
        return create_campaign_with_streams(
            db=db,
            client=client,
            name=body.name,
            geo=body.geo,
            offer_id=body.offer_id,
        )
    except KeitaroNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except CampaignServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except KeitaroAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": str(exc),
                "keitaro_status": exc.status_code,
                "keitaro_payload": exc.payload,
            },
        ) from exc


@router.get("", response_model=list[CampaignResponse])
def list_campaigns(db: Session = Depends(get_db)) -> list[Campaign]:
    stmt = select(Campaign).order_by(Campaign.created_at.desc())
    return list(db.scalars(stmt).all())


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)) -> Campaign:
    record = db.get(Campaign, campaign_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return record
