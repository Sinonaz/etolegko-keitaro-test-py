from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StreamDraft(Base):
    """Local mirror of a Keitaro stream for one campaign."""

    __tablename__ = "stream_drafts"
    __table_args__ = (
        UniqueConstraint("campaign_id", "keitaro_stream_id", name="uq_stream_draft"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keitaro_stream_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    stream_type: Mapped[str] = mapped_column(String(32), nullable=False, default="regular")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    schema: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    filter_summary: Mapped[str] = mapped_column(String(255), nullable=False, default="None")
    editable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class StreamOfferDraft(Base):
    """Offer row inside a stream draft (supports soft-remove + pin)."""

    __tablename__ = "stream_offer_drafts"
    __table_args__ = (
        UniqueConstraint("stream_draft_id", "offer_id", name="uq_stream_offer"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    stream_draft_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("stream_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    offer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    offer_name: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    share: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    removed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
