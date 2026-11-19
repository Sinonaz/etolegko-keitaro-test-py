"""create campaigns table

Revision ID: 20261119_0001
Revises:
Create Date: 2026-11-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261119_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("geo", sa.String(length=8), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("keitaro_campaign_id", sa.Integer(), nullable=False),
        sa.Column("keitaro_alias", sa.String(length=128), nullable=False),
        sa.Column("geo_stream_id", sa.Integer(), nullable=True),
        sa.Column("offer_stream_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("keitaro_campaign_id"),
    )


def downgrade() -> None:
    op.drop_table("campaigns")
