"""stream drafts for offers editor

Revision ID: 20261119_0002
Revises: 20261119_0001
Create Date: 2026-11-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261119_0002"
down_revision: Union[str, None] = "20261119_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stream_drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("campaign_id", sa.String(length=36), nullable=False),
        sa.Column("keitaro_stream_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("stream_type", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("schema", sa.String(length=32), nullable=False),
        sa.Column("filter_summary", sa.String(length=255), nullable=False),
        sa.Column("editable", sa.Boolean(), nullable=False),
        sa.Column("dirty", sa.Boolean(), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "keitaro_stream_id", name="uq_stream_draft"),
    )
    op.create_index("ix_stream_drafts_campaign_id", "stream_drafts", ["campaign_id"])

    op.create_table(
        "stream_offer_drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("stream_draft_id", sa.String(length=36), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("offer_name", sa.String(length=512), nullable=False),
        sa.Column("share", sa.Integer(), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("removed", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["stream_draft_id"], ["stream_drafts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stream_draft_id", "offer_id", name="uq_stream_offer"),
    )
    op.create_index(
        "ix_stream_offer_drafts_stream_draft_id",
        "stream_offer_drafts",
        ["stream_draft_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_stream_offer_drafts_stream_draft_id",
        table_name="stream_offer_drafts",
    )
    op.drop_table("stream_offer_drafts")
    op.drop_index("ix_stream_drafts_campaign_id", table_name="stream_drafts")
    op.drop_table("stream_drafts")
