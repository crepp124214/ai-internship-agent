"""add interview question sets

Revision ID: 009_interview_question_sets
Revises: 008
Create Date: 2026-04-10 21:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "009_interview_question_sets"
down_revision: str | Sequence[str] | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_question_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("resume_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="generated"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("questions_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_question_sets_id"), "interview_question_sets", ["id"], unique=False)
    op.create_index(op.f("ix_interview_question_sets_job_id"), "interview_question_sets", ["job_id"], unique=False)
    op.create_index(op.f("ix_interview_question_sets_resume_id"), "interview_question_sets", ["resume_id"], unique=False)
    op.create_index(op.f("ix_interview_question_sets_source"), "interview_question_sets", ["source"], unique=False)
    op.create_index(op.f("ix_interview_question_sets_status"), "interview_question_sets", ["status"], unique=False)
    op.create_index(op.f("ix_interview_question_sets_user_id"), "interview_question_sets", ["user_id"], unique=False)
    op.create_index(op.f("ix_interview_question_sets_created_at"), "interview_question_sets", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_question_sets_created_at"), table_name="interview_question_sets")
    op.drop_index(op.f("ix_interview_question_sets_user_id"), table_name="interview_question_sets")
    op.drop_index(op.f("ix_interview_question_sets_status"), table_name="interview_question_sets")
    op.drop_index(op.f("ix_interview_question_sets_source"), table_name="interview_question_sets")
    op.drop_index(op.f("ix_interview_question_sets_resume_id"), table_name="interview_question_sets")
    op.drop_index(op.f("ix_interview_question_sets_job_id"), table_name="interview_question_sets")
    op.drop_index(op.f("ix_interview_question_sets_id"), table_name="interview_question_sets")
    op.drop_table("interview_question_sets")
