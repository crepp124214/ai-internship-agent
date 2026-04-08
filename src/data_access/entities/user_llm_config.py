"""
User LLM Config ORM entity.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import relationship

from src.data_access.database import Base


class UserLlmConfig(Base):
    """
    User LLM Configuration entity.

    Stores per-user, per-agent LLM configuration including provider,
    model, API key, and generation parameters.

    Attributes:
        id: Primary key
        user_id: Foreign key to users.id
        agent: Agent identifier (resume_agent / job_agent / interview_agent)
        provider: LLM provider name
        model: Model name
        api_key_encrypted: Encrypted API key
        base_url: Optional custom endpoint
        temperature: Generation temperature
        is_active: Whether this config is active
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "user_llm_configs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, comment="Config primary key")

    # Foreign key to user
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID",
    )

    # Agent identifier
    agent = Column(String(50), nullable=False, comment="Agent identifier")

    # Provider and model
    provider = Column(String(100), nullable=False, comment="LLM provider")
    model = Column(String(100), nullable=False, comment="Model name")

    # API key (encrypted)
    api_key_encrypted = Column(String(500), nullable=False, comment="Encrypted API key")

    # Optional custom endpoint
    base_url = Column(String(255), nullable=True, comment="Custom endpoint URL")

    # Generation parameters
    temperature = Column(Float, nullable=True, default=0.7, comment="Generation temperature")

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True, comment="Is active")

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="Created at",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Updated at",
    )

    # Relationship
    user = relationship("User", lazy="joined")

    # Composite indexes
    __table_args__ = (
        Index("idx_user_llm_config_user_agent", "user_id", "agent", unique=True),
    )

    def __repr__(self) -> str:
        """Return a compact debug representation."""
        return (
            f"<UserLlmConfig(user_id={self.user_id}, agent='{self.agent}', "
            f"provider='{self.provider}', model='{self.model}')>"
        )