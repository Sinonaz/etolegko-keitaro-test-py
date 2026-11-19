"""Fetch / edit / push Keitaro stream offers for a local campaign."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.campaign import Campaign
from app.models.stream_draft import StreamDraft, StreamOfferDraft
from app.schemas.streams import (
    StreamsEditorResponse,
    StreamOfferView,
    StreamView,
)
from app.services.keitaro.client import KeitaroClient
from app.services.keitaro.exceptions import KeitaroError
from app.services.weights import OfferShare, redistribute

JsonDict = dict[str, Any]


class StreamServiceError(KeitaroError):
    pass


def keitaro_admin_campaign_url(keitaro_campaign_id: int) -> str | None:
    base = get_settings().keitaro_url.rstrip("/")
    if not base:
        return None
    return f"{base}/admin/#!/campaigns/{keitaro_campaign_id}"


def _filter_summary(stream: JsonDict) -> str:
    filters = stream.get("filters") or []
    if not filters:
        return "None"
    parts: list[str] = []
    for item in filters:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or "?"
        mode = item.get("mode") or "?"
        payload = item.get("payload")
        if isinstance(payload, list):
            payload_s = ",".join(str(x) for x in payload)
        else:
            payload_s = str(payload or "")
        parts.append(f"{name}:{mode}:{payload_s}")
    return "; ".join(parts) or "None"


def _is_editable_stream(stream: JsonDict) -> bool:
    schema = str(stream.get("schema") or "").lower()
    offers = stream.get("offers") or []
    return schema in {"offers", "landings", "landings_offers"} or bool(offers)


def _offer_name_from_kt(offer: JsonDict) -> str:
    # Keitaro may nest offer info differently depending on version
    for key in ("name", "offer_name"):
        if offer.get(key):
            return str(offer[key])
    nested = offer.get("offer")
    if isinstance(nested, dict) and nested.get("name"):
        return str(nested["name"])
    oid = offer.get("offer_id") or offer.get("id")
    return f"Offer {oid}"


def _offer_id_from_kt(offer: JsonDict) -> int | None:
    for key in ("offer_id", "id"):
        if offer.get(key) is not None:
            try:
                return int(offer[key])
            except (TypeError, ValueError):
                continue
    return None


def _snapshot_offers(rows: list[StreamOfferDraft]) -> str:
    payload = [
        {
            "offer_id": row.offer_id,
            "offer_name": row.offer_name,
            "share": row.share,
            "pinned": row.pinned,
            "removed": row.removed,
            "sort_order": row.sort_order,
        }
        for row in sorted(rows, key=lambda r: r.sort_order)
    ]
    return json.dumps(payload)


def _apply_weights(rows: list[StreamOfferDraft]) -> None:
    shares = [
        OfferShare(
            offer_id=row.offer_id,
            share=row.share,
            pinned=row.pinned,
            removed=row.removed,
        )
        for row in rows
    ]
    redistribute(shares)
    by_id = {s.offer_id: s for s in shares}
    for row in rows:
        state = by_id[row.offer_id]
        row.share = state.share
        row.pinned = state.pinned
        row.removed = state.removed


def _get_campaign(db: Session, campaign_id: str) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise StreamServiceError("Campaign not found")
    return campaign


def _get_stream_draft(
    db: Session,
    campaign_id: str,
    keitaro_stream_id: int,
) -> StreamDraft:
    stmt = select(StreamDraft).where(
        StreamDraft.campaign_id == campaign_id,
        StreamDraft.keitaro_stream_id == keitaro_stream_id,
    )
    draft = db.scalars(stmt).first()
    if draft is None:
        raise StreamServiceError("Stream draft not found; fetch streams first")
    return draft


def _offer_rows(db: Session, stream_draft_id: str) -> list[StreamOfferDraft]:
    stmt = (
        select(StreamOfferDraft)
        .where(StreamOfferDraft.stream_draft_id == stream_draft_id)
        .order_by(StreamOfferDraft.sort_order, StreamOfferDraft.offer_id)
    )
    return list(db.scalars(stmt).all())


def build_editor_response(db: Session, campaign: Campaign) -> StreamsEditorResponse:
    stmt = (
        select(StreamDraft)
        .where(StreamDraft.campaign_id == campaign.id)
        .order_by(StreamDraft.position, StreamDraft.keitaro_stream_id)
    )
    drafts = list(db.scalars(stmt).all())
    streams: list[StreamView] = []
    for draft in drafts:
        offers = [
            StreamOfferView(
                offer_id=row.offer_id,
                offer_name=row.offer_name,
                share=row.share,
                pinned=row.pinned,
                removed=row.removed,
            )
            for row in _offer_rows(db, draft.id)
        ]
        streams.append(
            StreamView(
                keitaro_stream_id=draft.keitaro_stream_id,
                name=draft.name,
                stream_type=draft.stream_type,
                position=draft.position,
                schema=draft.schema,
                filter_summary=draft.filter_summary,
                editable=draft.editable,
                dirty=draft.dirty,
                offers=offers,
            )
        )

    return StreamsEditorResponse(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        keitaro_campaign_id=campaign.keitaro_campaign_id,
        keitaro_admin_url=keitaro_admin_campaign_url(campaign.keitaro_campaign_id),
        streams=streams,
    )


def fetch_streams(
    *,
    db: Session,
    client: KeitaroClient,
    campaign_id: str,
) -> StreamsEditorResponse:
    campaign = _get_campaign(db, campaign_id)
    remote_streams = client.list_campaign_streams(campaign.keitaro_campaign_id)

    # Clear previous drafts
    existing = db.scalars(
        select(StreamDraft).where(StreamDraft.campaign_id == campaign.id)
    ).all()
    for draft in existing:
        db.execute(
            delete(StreamOfferDraft).where(
                StreamOfferDraft.stream_draft_id == draft.id
            )
        )
        db.delete(draft)
    db.flush()

    for stream in remote_streams:
        stream_id = int(stream["id"])
        editable = _is_editable_stream(stream)
        draft = StreamDraft(
            campaign_id=campaign.id,
            keitaro_stream_id=stream_id,
            name=str(stream.get("name") or f"Stream {stream_id}"),
            stream_type=str(stream.get("type") or "regular"),
            position=int(stream.get("position") or 0),
            schema=str(stream.get("schema") or ""),
            filter_summary=_filter_summary(stream),
            editable=editable,
            dirty=False,
        )
        db.add(draft)
        db.flush()

        offer_rows: list[StreamOfferDraft] = []
        raw_offers = stream.get("offers") or []
        for index, raw in enumerate(raw_offers):
            if not isinstance(raw, dict):
                continue
            oid = _offer_id_from_kt(raw)
            if oid is None:
                continue
            state = str(raw.get("state") or "active").lower()
            removed = state in {"disabled", "deleted"}
            share = int(raw.get("share") or 0)
            row = StreamOfferDraft(
                stream_draft_id=draft.id,
                offer_id=oid,
                offer_name=_offer_name_from_kt(raw),
                share=0 if removed else share,
                pinned=False,
                removed=removed,
                sort_order=index,
            )
            db.add(row)
            offer_rows.append(row)

        if editable and offer_rows:
            _apply_weights(offer_rows)
        draft.snapshot_json = _snapshot_offers(offer_rows)

        # Keep campaign.offer_stream_id in sync when obvious
        if editable and campaign.offer_stream_id is None:
            campaign.offer_stream_id = stream_id

    db.commit()
    db.refresh(campaign)
    return build_editor_response(db, campaign)


def get_streams_editor(db: Session, campaign_id: str) -> StreamsEditorResponse:
    campaign = _get_campaign(db, campaign_id)
    return build_editor_response(db, campaign)


def add_offer(
    *,
    db: Session,
    client: KeitaroClient,
    campaign_id: str,
    keitaro_stream_id: int,
    offer_id: int,
) -> StreamsEditorResponse:
    campaign = _get_campaign(db, campaign_id)
    draft = _get_stream_draft(db, campaign_id, keitaro_stream_id)
    if not draft.editable:
        raise StreamServiceError("This stream is not editable")

    rows = _offer_rows(db, draft.id)
    for row in rows:
        if row.offer_id == offer_id:
            if row.removed:
                row.removed = False
                row.pinned = False
                _apply_weights(rows)
                draft.dirty = True
                db.commit()
                return build_editor_response(db, campaign)
            raise StreamServiceError(f"Offer {offer_id} already in stream")

    try:
        remote = client.get_offer(offer_id)
        offer_name = str(remote.get("name") or f"Offer {offer_id}")
    except Exception:
        offer_name = f"Offer {offer_id}"

    row = StreamOfferDraft(
        stream_draft_id=draft.id,
        offer_id=offer_id,
        offer_name=offer_name,
        share=0,
        pinned=False,
        removed=False,
        sort_order=(max((r.sort_order for r in rows), default=-1) + 1),
    )
    db.add(row)
    rows.append(row)
    _apply_weights(rows)
    draft.dirty = True
    db.commit()
    return build_editor_response(db, campaign)


def remove_offer(
    *,
    db: Session,
    campaign_id: str,
    keitaro_stream_id: int,
    offer_id: int,
) -> StreamsEditorResponse:
    campaign = _get_campaign(db, campaign_id)
    draft = _get_stream_draft(db, campaign_id, keitaro_stream_id)
    if not draft.editable:
        raise StreamServiceError("This stream is not editable")

    rows = _offer_rows(db, draft.id)
    target = next((r for r in rows if r.offer_id == offer_id), None)
    if target is None:
        raise StreamServiceError("Offer not found in stream")
    target.removed = True
    target.pinned = False
    _apply_weights(rows)
    draft.dirty = True
    db.commit()
    return build_editor_response(db, campaign)


def bring_back_offer(
    *,
    db: Session,
    campaign_id: str,
    keitaro_stream_id: int,
    offer_id: int,
) -> StreamsEditorResponse:
    campaign = _get_campaign(db, campaign_id)
    draft = _get_stream_draft(db, campaign_id, keitaro_stream_id)
    rows = _offer_rows(db, draft.id)
    target = next((r for r in rows if r.offer_id == offer_id), None)
    if target is None:
        raise StreamServiceError("Offer not found in stream")
    target.removed = False
    _apply_weights(rows)
    draft.dirty = True
    db.commit()
    return build_editor_response(db, campaign)


def set_offer_pin(
    *,
    db: Session,
    campaign_id: str,
    keitaro_stream_id: int,
    offer_id: int,
    pinned: bool,
) -> StreamsEditorResponse:
    campaign = _get_campaign(db, campaign_id)
    draft = _get_stream_draft(db, campaign_id, keitaro_stream_id)
    rows = _offer_rows(db, draft.id)
    target = next((r for r in rows if r.offer_id == offer_id), None)
    if target is None:
        raise StreamServiceError("Offer not found in stream")
    if target.removed:
        raise StreamServiceError("Cannot pin a removed offer")
    target.pinned = pinned
    _apply_weights(rows)
    draft.dirty = True
    db.commit()
    return build_editor_response(db, campaign)


def cancel_stream_edits(
    *,
    db: Session,
    campaign_id: str,
    keitaro_stream_id: int,
) -> StreamsEditorResponse:
    campaign = _get_campaign(db, campaign_id)
    draft = _get_stream_draft(db, campaign_id, keitaro_stream_id)

    db.execute(
        delete(StreamOfferDraft).where(StreamOfferDraft.stream_draft_id == draft.id)
    )
    snapshot = json.loads(draft.snapshot_json or "[]")
    for index, item in enumerate(snapshot):
        db.add(
            StreamOfferDraft(
                stream_draft_id=draft.id,
                offer_id=int(item["offer_id"]),
                offer_name=str(item.get("offer_name") or ""),
                share=int(item.get("share") or 0),
                pinned=bool(item.get("pinned")),
                removed=bool(item.get("removed")),
                sort_order=int(item.get("sort_order", index)),
            )
        )
    draft.dirty = False
    db.commit()
    return build_editor_response(db, campaign)


def push_stream(
    *,
    db: Session,
    client: KeitaroClient,
    campaign_id: str,
    keitaro_stream_id: int,
) -> StreamsEditorResponse:
    campaign = _get_campaign(db, campaign_id)
    draft = _get_stream_draft(db, campaign_id, keitaro_stream_id)
    if not draft.editable:
        raise StreamServiceError("This stream is not editable")

    rows = _offer_rows(db, draft.id)
    active = [r for r in rows if not r.removed]
    if not active:
        raise StreamServiceError("Cannot push: no active offers")

    payload_offers = [
        {
            "offer_id": row.offer_id,
            "share": row.share,
            "state": "active",
        }
        for row in active
    ]
    # Ensure shares still sum to 100 before push
    total = sum(o["share"] for o in payload_offers)
    if total != 100:
        shares = [
            OfferShare(offer_id=r.offer_id, share=r.share, pinned=r.pinned, removed=False)
            for r in active
        ]
        redistribute(shares)
        by_id = {s.offer_id: s.share for s in shares}
        for row in active:
            row.share = by_id[row.offer_id]
        payload_offers = [
            {"offer_id": r.offer_id, "share": r.share, "state": "active"} for r in active
        ]

    client.update_stream(
        keitaro_stream_id,
        {
            "offers": payload_offers,
        },
    )

    # Drop removed rows after successful push; refresh snapshot
    for row in list(rows):
        if row.removed:
            db.delete(row)
    db.flush()
    remaining = _offer_rows(db, draft.id)
    draft.snapshot_json = _snapshot_offers(remaining)
    draft.dirty = False
    db.commit()
    return build_editor_response(db, campaign)
