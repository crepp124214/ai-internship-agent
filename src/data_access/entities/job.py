# -*- coding: utf-8 -*-
"""
Job-related persistence models.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.data_access.database import Base


class Job(Base):
    """
    Job posting entity.

    Stores the full job posting record, including the core description,
    company data, salary metadata, and source details.
    """

    __tablename__ = "jobs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, comment="Job primary key")

    # Core details
    title = Column(String(200), nullable=False, index=True, comment="Job title")
    company = Column(String(100), nullable=False, index=True, comment="Company name")
    company_logo = Column(String(500), comment="Company logo URL")
    location = Column(String(100), nullable=False, index=True, comment="Job location")

    # Salary details
    salary = Column(String(100), comment="Salary range text")
    salary_min = Column(Numeric(10, 2), comment="Minimum salary")
    salary_max = Column(Numeric(10, 2), comment="Maximum salary")

    # Job requirements
    work_type = Column(String(50), index=True, comment="Work type")
    experience = Column(String(50), index=True, comment="Experience requirement")
    education = Column(String(50), index=True, comment="Education requirement")

    # Long-form content
    description = Column(Text, comment="Job description")
    requirements = Column(Text, comment="Job requirements")
    welfare = Column(Text, comment="Benefits")
    tags = Column(String(500), comment="Comma-separated tags")

    # Source details
    source = Column(String(50), nullable=False, index=True, comment="Source platform")
    source_url = Column(String(500), comment="Source URL")
    source_id = Column(String(100), comment="Source platform ID")

    # Status
    is_active = Column(Boolean, default=True, index=True, comment="Whether the job is active")

    # Timestamps
    publish_date = Column(DateTime, index=True, comment="Published at")
    deadline = Column(DateTime, index=True, comment="Application deadline")
    created_at = Column(DateTime, default=datetime.now, index=True, comment="Created at")
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="Updated at",
    )

    # Relationships
    job_applications = relationship(
        "JobApplication",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    job_match_results = relationship(
        "JobMatchResult",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    interview_records = relationship("InterviewRecord", back_populates="job", lazy="dynamic")
    interview_sessions = relationship("InterviewSession", back_populates="job", lazy="dynamic")

    # Composite indexes
    __table_args__ = (
        Index("idx_job_company_location", "company", "location"),
        Index("idx_job_work_type_experience", "work_type", "experience"),
        Index("idx_job_source_active", "source", "is_active"),
        Index("idx_job_publish_active", "publish_date", "is_active"),
    )

    def __repr__(self) -> str:
        """Return a compact debug representation."""
        return f"<Job(id={self.id}, title='{self.title}', company='{self.company}')>"

    def get_salary_range(self) -> str:
        """Return a human-readable salary range string."""
        if self.salary_min and self.salary_max:
            return f"{self.salary_min}-{self.salary_max}"
        if self.salary:
            return self.salary
        return "Negotiable"

    def is_salary_in_range(self, min_salary: float, max_salary: float) -> bool:
        """Check whether the stored salary range is inside the given range."""
        if self.salary_min and self.salary_max:
            return self.salary_min >= min_salary and self.salary_max <= max_salary
        return False


class JobApplication(Base):
    """Application record for a job."""

    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True, comment="Application ID")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID",
    )
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Job ID",
    )
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        comment="Resume ID",
    )

    application_date = Column(DateTime, default=datetime.now, index=True, comment="Applied at")
    status = Column(String(50), default="applied", index=True, comment="Application status")
    status_updated_at = Column(DateTime, default=datetime.now, comment="Status updated at")
    notes = Column(Text, comment="Notes")

    created_at = Column(DateTime, default=datetime.now, comment="Created at")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="Updated at")

    user = relationship("User", back_populates="job_applications", lazy="joined")
    job = relationship("Job", back_populates="job_applications", lazy="joined")
    resume = relationship("Resume", back_populates="job_applications", lazy="joined")

    __table_args__ = (
        Index("idx_application_user_status", "user_id", "status"),
        Index("idx_application_job_status", "job_id", "status"),
        Index("idx_application_date_status", "application_date", "status"),
    )

    def __repr__(self) -> str:
        return f"<JobApplication(id={self.id}, user_id={self.user_id}, job_id={self.job_id}, status='{self.status}')>"

    def is_successful(self) -> bool:
        return self.status in ["accepted", "hired", "offer"]

    def is_pending(self) -> bool:
        return self.status in ["applied", "reviewing", "interviewing"]

    def is_rejected(self) -> bool:
        return self.status in ["rejected", "declined"]


class JobMatchResult(Base):
    """Persisted job match result."""

    __tablename__ = "job_match_results"

    id = Column(Integer, primary_key=True, index=True, comment="Match result ID")
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Related job ID",
    )
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Related resume ID",
    )
    mode = Column(String(50), nullable=False, default="job_match", comment="Match mode")
    score = Column(Integer, nullable=False, index=True, comment="Match score")
    feedback = Column(Text, nullable=False, comment="Match feedback")
    raw_content = Column(Text, nullable=False, comment="Raw LLM output")
    provider = Column(String(50), nullable=False, comment="LLM provider")
    model = Column(String(100), nullable=False, comment="LLM model")

    created_at = Column(DateTime, default=datetime.now, index=True, comment="Created at")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="Updated at")

    job = relationship("Job", back_populates="job_match_results", lazy="joined")
    resume = relationship("Resume", back_populates="job_match_results", lazy="joined")

    __table_args__ = (
        Index("idx_job_match_result_job_created", "job_id", "created_at"),
        Index("idx_job_match_result_job_mode", "job_id", "mode"),
        Index("idx_job_match_result_resume_created", "resume_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<JobMatchResult(id={self.id}, job_id={self.job_id}, resume_id={self.resume_id}, "
            f"mode='{self.mode}', provider='{self.provider}', model='{self.model}')>"
        )
