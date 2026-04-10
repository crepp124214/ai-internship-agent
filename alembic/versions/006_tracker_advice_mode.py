"""add mode column to tracker advice

Revision ID: 006_tracker_advice_mode
Revises: 005_interview_record_provider_model
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa


revision = "006_tracker_advice_mode"
down_revision = "005_interview_provider_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("tracker_advices")}
    existing_indexes = {index["name"] for index in inspector.get_indexes("tracker_advices")}

    if "mode" not in existing_columns:
        op.add_column(
            "tracker_advices",
            sa.Column("mode", sa.String(length=50), nullable=False, server_default="tracker_advice"),
        )

    if op.f("ix_tracker_advices_mode") not in existing_indexes:
        op.create_index(op.f("ix_tracker_advices_mode"), "tracker_advices", ["mode"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("tracker_advices")}
    existing_indexes = {index["name"] for index in inspector.get_indexes("tracker_advices")}

    if op.f("ix_tracker_advices_mode") in existing_indexes:
        op.drop_index(op.f("ix_tracker_advices_mode"), table_name="tracker_advices")

    if "mode" in existing_columns:
        op.drop_column("tracker_advices", "mode")
