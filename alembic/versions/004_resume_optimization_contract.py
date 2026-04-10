"""align resume optimization with shared AI result contract

Revision ID: 004_resume_optimization_contract
Revises: 003_job_match_result
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa


revision = "004_resume_opt_contract"
down_revision = "003_job_match_result"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resume_optimizations",
        sa.Column(
            "mode",
            sa.String(length=50),
            nullable=True,
            server_default=sa.text("'resume_improvements'"),
        ),
    )
    op.add_column(
        "resume_optimizations",
        sa.Column(
            "raw_content",
            sa.Text(),
            nullable=True,
            server_default=sa.text("''"),
        ),
    )
    op.add_column(
        "resume_optimizations",
        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=True,
            server_default=sa.text("'unknown-provider'"),
        ),
    )
    op.add_column(
        "resume_optimizations",
        sa.Column(
            "model",
            sa.String(length=100),
            nullable=True,
            server_default=sa.text("'unknown-model'"),
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE resume_optimizations
            SET
                mode = COALESCE(mode, 'resume_improvements'),
                raw_content = COALESCE(raw_content, ai_suggestion, optimized_text, original_text, ''),
                provider = COALESCE(provider, 'unknown-provider'),
                model = COALESCE(model, 'unknown-model')
            """
        )
    )


def downgrade() -> None:
    op.drop_column("resume_optimizations", "model")
    op.drop_column("resume_optimizations", "provider")
    op.drop_column("resume_optimizations", "raw_content")
    op.drop_column("resume_optimizations", "mode")
