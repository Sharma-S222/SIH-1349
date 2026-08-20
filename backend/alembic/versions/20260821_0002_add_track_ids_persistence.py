"""Add track_ids and persistence_ms columns to event table.

Revision ID: 20260821_0002
Revises: 20260820_0001
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260821_0002"
down_revision = "20260820_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("event", sa.Column("track_ids", sa.Text(), nullable=True))
    op.add_column("event", sa.Column("persistence_ms", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("event", "persistence_ms")
    op.drop_column("event", "track_ids")