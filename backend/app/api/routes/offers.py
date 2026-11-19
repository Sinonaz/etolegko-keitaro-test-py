from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.campaign import OfferSuggestion
from app.services.keitaro import (
    KeitaroAPIError,
    KeitaroClient,
    KeitaroNotConfiguredError,
    get_keitaro_client,
)

router = APIRouter(prefix="/offers")


@router.get("/search", response_model=list[OfferSuggestion])
def search_offers(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=15, ge=1, le=50),
    client: KeitaroClient = Depends(get_keitaro_client),
) -> list[OfferSuggestion]:
    try:
        offers = client.search_offers(q, limit=limit)
    except KeitaroNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except KeitaroAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    result: list[OfferSuggestion] = []
    for offer in offers:
        try:
            result.append(
                OfferSuggestion(
                    id=int(offer["id"]),
                    name=str(offer.get("name") or f"Offer {offer['id']}"),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return result
