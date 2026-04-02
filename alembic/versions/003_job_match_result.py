"""add job match result table

Revision ID: 003_job_match_result
Revises: 002_tracker_advice
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa


revision = "003_job_match_result"
down_revision = "002_tracker_advice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_match_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_match_results_id"), "job_match_results", ["id"], unique=False)
    op.create_index(
        op.f("ix_job_match_results_job_id"),
        "job_match_results",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_match_results_resume_id"),
        "job_match_results",
        ["resume_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_match_results_score"),
        "job_match_results",
        ["score"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_match_results_created_at"),
        "job_match_results",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "idx_job_match_result_job_created",
        "job_match_results",
        ["job_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_job_match_result_job_mode",
        "job_match_results",
        ["job_id", "mode"],
        unique=False,
    )
    op.create_index(
        "idx_job_match_result_resume_created",
        "job_match_results",
        ["resume_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_job_match_result_resume_created", table_name="job_match_results")
    op.drop_index("idx_job_match_result_job_mode", table_name="job_match_results")
    op.drop_index("idx_job_match_result_job_created", table_name="job_match_results")
    op.drop_index(op.f("ix_job_match_results_created_at"), table_name="job_match_results")
    op.drop_index(op.f("ix_job_match_results_score"), table_name="job_match_results")
    op.drop_index(op.f("ix_job_match_results_resume_id"), table_name="job_match_results")
    op.drop_index(op.f("ix_job_match_results_job_id"), table_name="job_match_results")
    op.drop_index(op.f("ix_job_match_results_id"), table_name="job_match_results")
    op.drop_table("job_match_results")
