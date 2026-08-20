"""Initial SIH1349 backend schema.

Revision ID: 20260820_0001
Revises:
Create Date: 2026-08-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "station",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("timezone", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_station_id"), "station", ["id"], unique=False)

    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("camera_id", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("zone_id", sa.String(length=100), nullable=True),
        sa.Column("people_count", sa.Integer(), nullable=True),
        sa.Column("raw_metadata", sa.Text(), server_default="{}", nullable=True),
        sa.Column("snapshot_path", sa.String(length=500), nullable=True),
        sa.Column("clip_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_event_camera_id", "event", ["camera_id"], unique=False)
    op.create_index("ix_event_event_type", "event", ["event_type"], unique=False)
    op.create_index(op.f("ix_event_id"), "event", ["id"], unique=False)
    op.create_index("ix_event_timestamp", "event", ["timestamp"], unique=False)

    op.create_table(
        "incident",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(op.f("ix_incident_id"), "incident", ["id"], unique=False)

    op.create_table(
        "crowd_metric",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camera_id", sa.String(length=50), nullable=False),
        sa.Column("zone_id", sa.String(length=100), nullable=True),
        sa.Column("people_count", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_crowd_metric_id"), "crowd_metric", ["id"], unique=False)

    op.create_table(
        "camera",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("zone_context", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["station_id"], ["station.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_camera_id"), "camera", ["id"], unique=False)

    op.create_table(
        "operator_action",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("user", sa.String(length=100), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["incident_id"], ["incident.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operator_action_id"), "operator_action", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_operator_action_id"), table_name="operator_action")
    op.drop_table("operator_action")
    op.drop_index(op.f("ix_camera_id"), table_name="camera")
    op.drop_table("camera")
    op.drop_index(op.f("ix_crowd_metric_id"), table_name="crowd_metric")
    op.drop_table("crowd_metric")
    op.drop_index(op.f("ix_incident_id"), table_name="incident")
    op.drop_table("incident")
    op.drop_index("ix_event_timestamp", table_name="event")
    op.drop_index(op.f("ix_event_id"), table_name="event")
    op.drop_index("ix_event_event_type", table_name="event")
    op.drop_index("ix_event_camera_id", table_name="event")
    op.drop_table("event")
    op.drop_index(op.f("ix_station_id"), table_name="station")
    op.drop_table("station")
