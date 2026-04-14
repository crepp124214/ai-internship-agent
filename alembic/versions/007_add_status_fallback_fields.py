"""add status and fallback_used fields to entities

Revision ID: 007_add_status_fallback_fields
Revises: 006_refresh_token
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa


revision = "007_add_status_fallback_fields"
down_revision = "006_refresh_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check existing columns before adding
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Add fields to resume_optimizations table
    resume_columns = {col["name"] for col in inspector.get_columns("resume_optimizations")}
    if "status" not in resume_columns:
        op.add_column(
            "resume_optimizations",
            sa.Column("status", sa.String(length=50), nullable=False, server_default="success"),
        )

    if "fallback_used" not in resume_columns:
        op.add_column(
            "resume_optimizations",
            sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default="false"),
        )

    # Add fields to job_match_results table
    job_match_columns = {col["name"] for col in inspector.get_columns("job_match_results")}
    if "status" not in job_match_columns:
        op.add_column(
            "job_match_results",
            sa.Column("status", sa.String(length=50), nullable=False, server_default="success"),
        )

    if "fallback_used" not in job_match_columns:
        op.add_column(
            "job_match_results",
            sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default="false"),
        )

    # Add fields to interview_records table
    interview_columns = {col["name"] for col in inspector.get_columns("interview_records")}
    if "status" not in interview_columns:
        op.add_column(
            "interview_records",
            sa.Column("status", sa.String(length=50), nullable=False, server_default="success"),
        )

    if "fallback_used" not in interview_columns:
        op.add_column(
            "interview_records",
            sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default="false"),
        )

    # Create indexes for the new columns
    indexes = {idx["name"] for idx in inspector.get_indexes("resume_optimizations")}
    if "ix_resume_optimizations_status" not in indexes:
        op.create_index(
            op.f("ix_resume_optimizations_status"),
            "resume_optimizations",
            ["status"],
            unique=False,
        )

    if "ix_resume_optimizations_fallback_used" not in indexes:
        op.create_index(
            op.f("ix_resume_optimizations_fallback_used"),
            "resume_optimizations",
            ["fallback_used"],
            unique=False,
        )

    job_match_indexes = {idx["name"] for idx in inspector.get_indexes("job_match_results")}
    if "ix_job_match_results_status" not in job_match_indexes:
        op.create_index(
            op.f("ix_job_match_results_status"),
            "job_match_results",
            ["status"],
            unique=False,
        )

    if "ix_job_match_results_fallback_used" not in job_match_indexes:
        op.create_index(
            op.f("ix_job_match_results_fallback_used"),
            "job_match_results",
            ["fallback_used"],
            unique=False,
        )

    interview_indexes = {idx["name"] for idx in inspector.get_indexes("interview_records")}
    if "ix_interview_records_status" not in interview_indexes:
        op.create_index(
            op.f("ix_interview_records_status"),
            "interview_records",
            ["status"],
            unique=False,
        )

    if "ix_interview_records_fallback_used" not in interview_indexes:
        op.create_index(
            op.f("ix_interview_records_fallback_used"),
            "interview_records",
            ["fallback_used"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Drop indexes first
    indexes = {idx["name"] for idx in inspector.get_indexes("resume_optimizations")}
    if "ix_resume_optimizations_status" in indexes:
        op.drop_index(op.f("ix_resume_optimizations_status"), table_name="resume_optimizations")

    if "ix_resume_optimizations_fallback_used" in indexes:
        op.drop_index(op.f("ix_resume_optimizations_fallback_used"), table_name="resume_optimizations")

    job_match_indexes = {idx["name"] for idx in inspector.get_indexes("job_match_results")}
    if "ix_job_match_results_status" in job_match_indexes:
        op.drop_index(op.f("ix_job_match_results_status"), table_name="job_match_results")

    if "ix_job_match_results_fallback_used" in job_match_indexes:
        op.drop_index(op.f("ix_job_match_results_fallback_used"), table_name="job_match_results")

    interview_indexes = {idx["name"] for idx in inspector.get_indexes("interview_records")}
    if "ix_interview_records_status" in interview_indexes:
        op.drop_index(op.f("ix_interview_records_status"), table_name="interview_records")

    if "ix_interview_records_fallback_used" in interview_indexes:
        op.drop_index(op.f("ix_interview_records_fallback_used"), table_name="interview_records")

    # Drop columns
    op.drop_column("resume_optimizations", "fallback_used")
    op.drop_column("resume_optimizations", "status")
    op.drop_column("job_match_results", "fallback_used")
    op.drop_column("job_match_results", "status")
    op.drop_column("interview_records", "fallback_used")
    op.drop_column("interview_records", "status")
