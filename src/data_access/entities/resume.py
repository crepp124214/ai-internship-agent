"""Resume persistence entities."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from src.data_access.database import Base


class Resume(Base):
    """Uploaded resume owned by a user."""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, comment="Resume ID")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID",
    )

    title = Column(String(200), nullable=False, comment="Resume title")
    original_file_path = Column(String(500), nullable=False, comment="Original file path")
    file_name = Column(String(255), nullable=False, comment="Original file name")
    file_type = Column(String(20), nullable=False, index=True, comment="File extension/type")
    file_size = Column(Integer, comment="File size in bytes")

    processed_content = Column(Text, comment="Processed structured content")
    resume_text = Column(Text, comment="Extracted plain text content")
    language = Column(String(20), default="zh-CN", index=True, comment="Resume language")
    is_default = Column(Boolean, default=False, index=True, comment="Whether this is the default resume")

    created_at = Column(DateTime, default=datetime.now, index=True, comment="Created at")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="Updated at")

    user = relationship("User", back_populates="resumes", lazy="joined")
    resume_optimizations = relationship(
        "ResumeOptimization",
        back_populates="resume",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    job_match_results = relationship(
        "JobMatchResult",
        back_populates="resume",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    job_applications = relationship("JobApplication", back_populates="resume", lazy="dynamic")

    __table_args__ = (
        Index("idx_resume_user_default", "user_id", "is_default"),
        Index("idx_resume_user_language", "user_id", "language"),
    )

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, title='{self.title}', user_id={self.user_id})>"

    def get_file_extension(self) -> str:
        return self.file_type.lower() if self.file_type else ""

    def is_supported_format(self) -> bool:
        return self.get_file_extension() in ["pdf", "docx", "txt", "doc"]

    def get_file_size_human(self) -> str:
        if self.file_size is None:
            return "unknown"

        size = float(self.file_size)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"


class ResumeOptimization(Base):
    """Persisted AI optimization result for a resume."""

    __tablename__ = "resume_optimizations"

    id = Column(Integer, primary_key=True, index=True, comment="Optimization record ID")
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Related resume ID",
    )

    original_text = Column(Text, comment="Original resume text")
    optimized_text = Column(Text, comment="Optimized resume text")
    optimization_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Optimization type",
    )
    keywords = Column(String(500), comment="Extracted or targeted keywords")

    score = Column(Integer, index=True, comment="Optimization score 0-100")
    ai_suggestion = Column(Text, comment="Human-readable AI suggestion")
    mode = Column(
        String(50),
        nullable=False,
        default="resume_improvements",
        index=True,
        comment="AI result mode",
    )
    raw_content = Column(Text, nullable=False, default="", comment="Raw LLM output")
    provider = Column(
        String(50),
        nullable=False,
        default="unknown-provider",
        index=True,
        comment="LLM provider",
    )
    model = Column(
        String(100),
        nullable=False,
        default="unknown-model",
        index=True,
        comment="LLM model",
    )

    created_at = Column(DateTime, default=datetime.now, index=True, comment="Created at")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="Updated at")

    resume = relationship("Resume", back_populates="resume_optimizations", lazy="joined")

    def validate_score(self) -> None:
        if self.score is not None and (self.score < 0 or self.score > 100):
            raise ValueError(f"score must be within 0-100, got {self.score}")

    def __repr__(self) -> str:
        return (
            f"<ResumeOptimization(id={self.id}, resume_id={self.resume_id}, "
            f"type='{self.optimization_type}', provider='{self.provider}', model='{self.model}')>"
        )
