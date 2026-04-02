"""add provider/model metadata to interview records

Revision ID: 005_interview_record_provider_model
Revises: 004_resume_optimization_contract
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa


revision = "005_interview_record_provider_model"
down_revision = "004_resume_optimization_contract"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interview_records",
        sa.Column("provider", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "interview_records",
        sa.Column("model", sa.String(length=100), nullable=True),
    )
    op.create_index(
        op.f("ix_interview_records_provider"),
        "interview_records",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_interview_records_model"),
        "interview_records",
        ["model"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_records_model"), table_name="interview_records")
    op.drop_index(op.f("ix_interview_records_provider"), table_name="interview_records")
    op.drop_column("interview_records", "model")
    op.drop_column("interview_records", "provider")
