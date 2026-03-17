"""Initial schema — parent_profiles, health_logs, scheduled_reminders.

Revision ID: 001
Revises:
Create Date: 2026-03-16

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parent_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_phone", sa.String(20), nullable=False),
        sa.Column("caregiver_phone", sa.String(20), nullable=False),
        sa.Column("parent_name", sa.String(100), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("known_conditions", sa.JSON(), nullable=True),
        sa.Column("medications", sa.JSON(), nullable=True),
        sa.Column("preferred_language", sa.String(5), nullable=False, server_default="te"),
        sa.Column("checkin_time", sa.Time(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parent_profiles_parent_phone", "parent_profiles", ["parent_phone"], unique=True)
    op.create_index("ix_parent_profiles_caregiver_phone", "parent_profiles", ["caregiver_phone"])

    op.create_table(
        "health_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("log_type", sa.String(20), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("risk_level", sa.String(10), nullable=False, server_default="low"),
        sa.ForeignKeyConstraint(["parent_id"], ["parent_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_logs_parent_id", "health_logs", ["parent_id"])

    op.create_table(
        "scheduled_reminders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("reminder_type", sa.String(20), nullable=False),
        sa.Column("scheduled_time", sa.DateTime(), nullable=False),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("message_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["parent_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scheduled_reminders_parent_id", "scheduled_reminders", ["parent_id"])


def downgrade() -> None:
    op.drop_table("scheduled_reminders")
    op.drop_table("health_logs")
    op.drop_table("parent_profiles")
