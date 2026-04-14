"""backfill status and fallback_used columns on existing sqlite databases

Revision ID: 010_backfill_status_fallback_columns
Revises: 009_interview_question_sets
Create Date: 2026-04-10 23:55:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "010_backfill_status_fallback_columns"
down_revision: str | Sequence[str] | None = "009_interview_question_sets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ensure_columns(
    table_name: str,
    *,
    status_default: str = "success",
    fallback_default: str = "false",
) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}

    if "status" not in existing_columns:
        op.add_column(
            table_name,
            sa.Column("status", sa.String(length=50), nullable=False, server_default=status_default),
        )
    if "fallback_used" not in existing_columns:
        op.add_column(
            table_name,
            sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=fallback_default),
        )

    status_index = op.f(f"ix_{table_name}_status")
    fallback_index = op.f(f"ix_{table_name}_fallback_used")
    if status_index not in existing_indexes:
        op.create_index(status_index, table_name, ["status"], unique=False)
    if fallback_index not in existing_indexes:
        op.create_index(fallback_index, table_name, ["fallback_used"], unique=False)


def upgrade() -> None:
    _ensure_columns("job_match_results")
    _ensure_columns("resume_optimizations")
    _ensure_columns("interview_records")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name in ("interview_records", "resume_optimizations", "job_match_results"):
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}

        fallback_index = op.f(f"ix_{table_name}_fallback_used")
        status_index = op.f(f"ix_{table_name}_status")
        if fallback_index in existing_indexes:
            op.drop_index(fallback_index, table_name=table_name)
        if status_index in existing_indexes:
            op.drop_index(status_index, table_name=table_name)

        if "fallback_used" in existing_columns:
            op.drop_column(table_name, "fallback_used")
        if "status" in existing_columns:
            op.drop_column(table_name, "status")
