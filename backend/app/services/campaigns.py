"""Business logic: create Keitaro campaign with geo→Google + default offer streams."""

from __future__ import annotations

import re
import secrets
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.campaign import Campaign
from app.services.keitaro.client import KeitaroClient
from app.services.keitaro.exceptions import KeitaroAPIError, KeitaroError

JsonDict = dict[str, Any]


class CampaignServiceError(KeitaroError):
    """Domain error while creating a campaign."""


def make_alias(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "campaign"
    return f"{base}-{secrets.token_hex(3)}"


def _find_by_name(items: list[JsonDict], name: str) -> JsonDict | None:
    target = name.strip().lower()
    if not target:
        return None
    for item in items:
        if str(item.get("name", "")).strip().lower() == target:
            return item
    return None


def _find_domain(items: list[JsonDict], name_hint: str) -> JsonDict | None:
    hint = name_hint.strip().lower()
    if hint:
        for item in items:
            hay = str(item.get("name", "")).lower()
            if hint in hay:
                return item
    # Prefer first non-deleted looking domain
    for item in items:
        state = str(item.get("state", "active")).lower()
        if state != "deleted":
            return item
    return items[0] if items else None


def resolve_campaign_defaults(
    client: KeitaroClient,
    settings: Settings | None = None,
) -> tuple[int, int | str, int]:
    """Return (domain_id, group_id, traffic_source_id)."""
    settings = settings or get_settings()

    domain_id = settings.keitaro_domain_id
    if domain_id is None:
        domain = _find_domain(client.list_domains(), settings.keitaro_domain_name)
        if domain is None or "id" not in domain:
            raise CampaignServiceError(
                "No Keitaro domain found; set KEITARO_DOMAIN_ID or KEITARO_DOMAIN_NAME"
            )
        domain_id = int(domain["id"])

    group_id: int | str | None = settings.keitaro_group_id
    if group_id is None:
        group = _find_by_name(
            client.list_groups("campaigns"),
            settings.keitaro_group_name,
        )
        if group is None or "id" not in group:
            raise CampaignServiceError(
                f"Campaign group '{settings.keitaro_group_name}' not found; "
                "set KEITARO_GROUP_ID"
            )
        group_id = group["id"]

    source_id = settings.keitaro_source_id
    if source_id is None:
        source = _find_by_name(
            client.list_traffic_sources(),
            settings.keitaro_source_name,
        )
        if source is None or "id" not in source:
            raise CampaignServiceError(
                f"Traffic source '{settings.keitaro_source_name}' not found; "
                "set KEITARO_SOURCE_ID"
            )
        source_id = int(source["id"])

    return domain_id, group_id, source_id


def create_campaign_with_streams(
    *,
    db: Session,
    client: KeitaroClient,
    name: str,
    geo: str,
    offer_id: int,
    settings: Settings | None = None,
) -> Campaign:
    settings = settings or get_settings()
    domain_id, group_id, source_id = resolve_campaign_defaults(client, settings)
    alias = make_alias(name)

    # Verify offer exists early (clearer error than stream create failure)
    try:
        client.get_offer(offer_id)
    except KeitaroAPIError as exc:
        raise CampaignServiceError(f"Offer {offer_id} not found in Keitaro") from exc

    campaign_payload: JsonDict = {
        "name": name,
        "alias": alias,
        "type": "position",
        "state": "active",
        "domain_id": domain_id,
        "group_id": str(group_id),
        "traffic_source_id": source_id,
        "cost_type": "CPC",
        "cost_value": 0,
        "cost_auto": True,
    }

    created = client.create_campaign(campaign_payload)
    campaign_id = int(created["id"])

    geo_stream = client.create_stream(
        {
            "campaign_id": campaign_id,
            "type": "regular",
            "name": f"Geo {geo} → Google",
            "position": 1,
            "schema": "action",
            "action_type": "http",
            "action_payload": settings.keitaro_white_page_url,
            "collect_clicks": True,
            "filters": [
                {
                    "name": "country",
                    "mode": "accept",
                    "payload": [geo],
                }
            ],
        }
    )

    offer_stream = client.create_stream(
        {
            "campaign_id": campaign_id,
            "type": "default",
            "name": "Default offers",
            "position": 2,
            "schema": "offers",
            "action_type": "http",
            "action_payload": "",
            "collect_clicks": True,
            "offers": [
                {
                    "offer_id": offer_id,
                    "share": 100,
                    "state": "active",
                }
            ],
        }
    )

    record = Campaign(
        name=name,
        geo=geo,
        offer_id=offer_id,
        keitaro_campaign_id=campaign_id,
        keitaro_alias=str(created.get("alias") or alias),
        geo_stream_id=int(geo_stream["id"]) if geo_stream.get("id") is not None else None,
        offer_stream_id=(
            int(offer_stream["id"]) if offer_stream.get("id") is not None else None
        ),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
