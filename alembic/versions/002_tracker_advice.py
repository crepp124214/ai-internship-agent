"""add tracker advice table

Revision ID: 002_tracker_advice
Revises: 001_initial_schema
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa


revision = "002_tracker_advice"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tracker_advices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False, server_default="tracker_advice"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("next_steps", sa.Text(), nullable=False),
        sa.Column("risks", sa.Text(), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["job_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tracker_advices_id"), "tracker_advices", ["id"], unique=False)
    op.create_index(
        op.f("ix_tracker_advices_application_id"),
        "tracker_advices",
        ["application_id"],
        unique=False,
    )
    op.create_index(op.f("ix_tracker_advices_mode"), "tracker_advices", ["mode"], unique=False)
    op.create_index(op.f("ix_tracker_advices_provider"), "tracker_advices", ["provider"], unique=False)
    op.create_index(op.f("ix_tracker_advices_model"), "tracker_advices", ["model"], unique=False)
    op.create_index(
        op.f("ix_tracker_advices_created_at"),
        "tracker_advices",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tracker_advices_created_at"), table_name="tracker_advices")
    op.drop_index(op.f("ix_tracker_advices_model"), table_name="tracker_advices")
    op.drop_index(op.f("ix_tracker_advices_provider"), table_name="tracker_advices")
    op.drop_index(op.f("ix_tracker_advices_mode"), table_name="tracker_advices")
    op.drop_index(op.f("ix_tracker_advices_application_id"), table_name="tracker_advices")
    op.drop_index(op.f("ix_tracker_advices_id"), table_name="tracker_advices")
    op.drop_table("tracker_advices")
