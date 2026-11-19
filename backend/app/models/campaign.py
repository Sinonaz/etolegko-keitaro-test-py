from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Campaign(Base):
    """Local record of a campaign created via the wrapper."""

    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    geo: Mapped[str] = mapped_column(String(8), nullable=False)
    offer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    keitaro_campaign_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    keitaro_alias: Mapped[str] = mapped_column(String(128), nullable=False)
    geo_stream_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    offer_stream_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
