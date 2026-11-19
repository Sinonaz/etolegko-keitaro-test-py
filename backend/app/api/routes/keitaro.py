import httpx
from fastapi import APIRouter, Depends

from app.schemas.keitaro import KeitaroStatusResponse
from app.services.keitaro import (
    KeitaroAPIError,
    KeitaroClient,
    KeitaroNotConfiguredError,
    get_keitaro_client,
)

router = APIRouter(prefix="/keitaro")


@router.get("/status", response_model=KeitaroStatusResponse)
def keitaro_status(
    client: KeitaroClient = Depends(get_keitaro_client),
) -> KeitaroStatusResponse:
    """Check env config and optionally ping Keitaro Admin API."""
    if not client.is_configured:
        return KeitaroStatusResponse(
            configured=False,
            reachable=None,
            keitaro_url=None,
            error="KEITARO_URL and KEITARO_API_KEY are required",
        )

    try:
        client.ping()
        return KeitaroStatusResponse(
            configured=True,
            reachable=True,
            keitaro_url=client.base_url,
            error=None,
        )
    except (KeitaroNotConfiguredError, KeitaroAPIError, httpx.HTTPError, OSError) as exc:
        return KeitaroStatusResponse(
            configured=True,
            reachable=False,
            keitaro_url=client.base_url,
            error=str(exc),
        )
