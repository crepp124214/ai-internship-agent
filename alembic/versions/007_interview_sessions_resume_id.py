"""Add session_id/question_index/is_followup to interview_records, and resume_id/status/etc to interview_sessions.

Revision ID: 007
Revises: 007_add_status_fallback_fields
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "007_add_status_fallback_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility (SQLite doesn't support ALTER TABLE for FK constraints)

    # First, update interview_sessions to add missing columns
    with op.batch_alter_table("interview_sessions") as batch_op:
        # Add resume_id column (FK to resumes.id) - must name constraint explicitly for batch mode
        batch_op.add_column(
            sa.Column(
                "resume_id",
                sa.Integer(),
                sa.ForeignKey("resumes.id", ondelete="SET NULL", name="fk_interview_sessions_resume_id"),
                nullable=True,
                comment="Related resume ID",
            )
        )
        batch_op.create_index("ix_interview_sessions_resume_id", ["resume_id"], unique=False)

        # Add jd_text column
        batch_op.add_column(
            sa.Column("jd_text", sa.Text(), nullable=True, comment="Full JD text for this session")
        )

        # Add status column
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
                server_default="active",
                comment="Session status: active/completed/paused",
            )
        )
        batch_op.create_index("ix_interview_sessions_status", ["status"], unique=False)

        # Add followup_completed column
        batch_op.add_column(
            sa.Column(
                "followup_completed",
                sa.Boolean(),
                nullable=False,
                server_default="0",
                comment="Whether follow-up round is done",
            )
        )

    # Then, update interview_records to add missing columns
    with op.batch_alter_table("interview_records") as batch_op:
        # Add session_id column (FK to interview_sessions.id)
        batch_op.add_column(
            sa.Column(
                "session_id",
                sa.Integer(),
                sa.ForeignKey("interview_sessions.id", ondelete="CASCADE", name="fk_interview_records_session_id"),
                nullable=True,
                comment="Related session ID",
            )
        )
        batch_op.create_index("ix_interview_records_session_id", ["session_id"], unique=False)

        # Add question_index column
        batch_op.add_column(
            sa.Column(
                "question_index",
                sa.Integer(),
                nullable=False,
                server_default="0",
                comment="Question order in session",
            )
        )

        # Add is_followup column
        batch_op.add_column(
            sa.Column(
                "is_followup",
                sa.Boolean(),
                nullable=False,
                server_default="0",
                comment="Whether this is a follow-up question",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("interview_records") as batch_op:
        batch_op.drop_column("is_followup")
        batch_op.drop_column("question_index")
        batch_op.drop_index("ix_interview_records_session_id")
        batch_op.drop_column("session_id")

    with op.batch_alter_table("interview_sessions") as batch_op:
        batch_op.drop_column("followup_completed")
        batch_op.drop_index("ix_interview_sessions_status")
        batch_op.drop_column("status")
        batch_op.drop_column("jd_text")
        batch_op.drop_index("ix_interview_sessions_resume_id")
        batch_op.drop_column("resume_id")
