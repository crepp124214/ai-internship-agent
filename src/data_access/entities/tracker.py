"""
Tracker persistence entities.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, Index
from sqlalchemy.orm import relationship

from src.data_access.database import Base


class TrackerAdvice(Base):
    """Persisted AI advice for a job application."""

    __tablename__ = "tracker_advices"

    id = Column(Integer, primary_key=True, index=True, comment="Advice record ID")
    application_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Related application ID",
    )
    mode = Column(String(50), nullable=False, default="tracker_advice", comment="Advice mode")
    summary = Column(Text, nullable=False, comment="Advice summary")
    next_steps = Column(JSON, nullable=False, comment="Next step suggestions")
    risks = Column(JSON, nullable=False, comment="Risk suggestions")
    raw_content = Column(Text, nullable=False, comment="Raw LLM output")
    provider = Column(String(50), nullable=False, comment="LLM provider")
    model = Column(String(100), nullable=False, comment="LLM model")

    created_at = Column(DateTime, default=datetime.now, index=True, comment="Created at")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="Updated at")

    application = relationship("JobApplication", back_populates="tracker_advices", lazy="joined")

    __table_args__ = (
        Index("idx_tracker_advice_application_created", "application_id", "created_at"),
        Index("idx_tracker_advice_application_mode", "application_id", "mode"),
    )

    def __repr__(self) -> str:
        return (
            f"<TrackerAdvice(id={self.id}, application_id={self.application_id}, "
            f"mode='{self.mode}', provider='{self.provider}', model='{self.model}')>"
        )
