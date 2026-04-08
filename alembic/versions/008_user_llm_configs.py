"""Add user_llm_configs table.

Revision ID: 008
Revises: 007_interview_sessions_resume_id
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_llm_configs",
        sa.Column("id", sa.Integer(), nullable=False, comment="主键"),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="用户 ID",
        ),
        sa.Column(
            "agent",
            sa.String(length=50),
            nullable=False,
            comment="Agent 标识：resume_agent / job_agent / interview_agent",
        ),
        sa.Column("provider", sa.String(length=100), nullable=False, comment="Provider 标识"),
        sa.Column("model", sa.String(length=100), nullable=False, comment="模型名称"),
        sa.Column(
            "api_key_encrypted",
            sa.String(length=500),
            nullable=False,
            comment="加密后的 API Key",
        ),
        sa.Column(
            "base_url",
            sa.String(length=255),
            nullable=True,
            comment="自定义 API endpoint",
        ),
        sa.Column(
            "temperature",
            sa.Float(),
            nullable=True,
            server_default="0.7",
            comment="生成温度",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="1",
            comment="是否启用",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_llm_configs_id",
        "user_llm_configs",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_user_llm_configs_user_id",
        "user_llm_configs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_user_llm_config_user_agent",
        "user_llm_configs",
        ["user_id", "agent"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_user_llm_config_user_agent", table_name="user_llm_configs")
    op.drop_index("ix_user_llm_configs_user_id", table_name="user_llm_configs")
    op.drop_index("ix_user_llm_configs_id", table_name="user_llm_configs")
    op.drop_table("user_llm_configs")
