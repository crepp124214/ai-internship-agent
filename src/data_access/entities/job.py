# -*- coding: utf-8 -*-
"""
宀椾綅妯″瀷
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, Float, ForeignKey, Boolean, Index, Numeric
from sqlalchemy.orm import relationship

from src.data_access.database import Base


class Job(Base):
    """
    宀椾綅瀹炰綋

    瀛樺偍鎷涜仒宀椾綅鐨勮缁嗕俊鎭紝鍖呮嫭鑱屼綅鎻忚堪銆佸叕鍙镐俊鎭€佽柂璧勭瓑銆?
    Attributes:
        id: 宀椾綅涓婚敭ID
        title: 鑱屼綅鏍囬
        company: 鍏徃鍚嶇О
        company_logo: 鍏徃Logo URL
        location: 宸ヤ綔鍦扮偣
        salary: 钖祫鑼冨洿
        salary_min: 钖祫涓嬮檺
        salary_max: 钖祫涓婇檺
        work_type: 宸ヤ綔绫诲瀷锛堝叏鑱?鍏艰亴/瀹炰範锛?        experience: 缁忛獙瑕佹眰
        education: 瀛﹀巻瑕佹眰
        description: 鑱屼綅鎻忚堪
        requirements: 鑱屼綅瑕佹眰
        welfare: 绂忓埄寰呴亣
        tags: 鏍囩锛岄€楀彿鍒嗛殧
        source: 鏉ユ簮骞冲彴
        source_url: 婧怳RL
        source_id: 婧愬钩鍙癐D
        is_active: 鏄惁婵€娲?        publish_date: 鍙戝竷鏃ユ湡
        deadline: 鎴鏃ユ湡
        created_at: 鍒涘缓鏃堕棿
        updated_at: 鏇存柊鏃堕棿
    """

    __tablename__ = "jobs"

    # 涓婚敭
    id = Column(Integer, primary_key=True, index=True, comment="宀椾綅涓婚敭ID")

    # 鍩烘湰淇℃伅
    title = Column(String(200), nullable=False, index=True, comment="鑱屼綅鏍囬")
    company = Column(String(100), nullable=False, index=True, comment="鍏徃鍚嶇О")
    company_logo = Column(String(500), comment="鍏徃Logo URL")
    location = Column(String(100), nullable=False, index=True, comment="宸ヤ綔鍦扮偣")

    # 钖祫淇℃伅
    salary = Column(String(100), comment="钖祫鑼冨洿")
    salary_min = Column(Numeric(10, 2), comment="钖祫涓嬮檺")
    salary_max = Column(Numeric(10, 2), comment="钖祫涓婇檺")

    # 鑱屼綅瑕佹眰
    work_type = Column(String(50), index=True, comment="宸ヤ綔绫诲瀷")
    experience = Column(String(50), index=True, comment="缁忛獙瑕佹眰")
    education = Column(String(50), index=True, comment="瀛﹀巻瑕佹眰")

    # 璇︾粏鍐呭
    description = Column(Text, comment="鑱屼綅鎻忚堪")
    requirements = Column(Text, comment="鑱屼綅瑕佹眰")
    welfare = Column(Text, comment="绂忓埄寰呴亣")
    tags = Column(String(500), comment="鏍囩锛岄€楀彿鍒嗛殧")

    # 鏉ユ簮淇℃伅
    source = Column(String(50), nullable=False, index=True, comment="鏉ユ簮骞冲彴")
    source_url = Column(String(500), comment="婧怳RL")
    source_id = Column(String(100), comment="婧愬钩鍙癐D")

    # Status
    is_active = Column(Boolean, default=True, index=True, comment="Is active")

    # 鏃堕棿淇℃伅
    publish_date = Column(DateTime, index=True, comment="鍙戝竷鏃ユ湡")
    deadline = Column(DateTime, index=True, comment="鎴鏃ユ湡")
    created_at = Column(DateTime, default=datetime.now, index=True, comment="鍒涘缓鏃堕棿")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="鏇存柊鏃堕棿")

    # 鍏崇郴鏄犲皠
    job_applications = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan", lazy="dynamic")
    job_match_results = relationship(
        "JobMatchResult",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    interview_records = relationship("InterviewRecord", back_populates="job", lazy="dynamic")
    interview_sessions = relationship("InterviewSession", back_populates="job", lazy="dynamic")

    # 澶嶅悎绱㈠紩
    __table_args__ = (
        Index('idx_job_company_location', 'company', 'location'),
        Index('idx_job_work_type_experience', 'work_type', 'experience'),
        Index('idx_job_source_active', 'source', 'is_active'),
        Index('idx_job_publish_active', 'publish_date', 'is_active'),
    )

    def __repr__(self) -> str:
        """宀椾綅瀵硅薄鐨勫瓧绗︿覆琛ㄧず"""
        return f"<Job(id={self.id}, title='{self.title}', company='{self.company}')>"

    def get_salary_range(self) -> str:
        """
        鑾峰彇钖祫鑼冨洿瀛楃涓?
        Returns:
            str: 钖祫鑼冨洿鎻忚堪
        """
        if self.salary_min and self.salary_max:
            return f"{self.salary_min}-{self.salary_max}"
        elif self.salary:
            return self.salary
        else:
            return "闈㈣"

    def is_salary_in_range(self, min_salary: float, max_salary: float) -> bool:
        """
        妫€鏌ヨ柂璧勬槸鍚﹀湪鎸囧畾鑼冨洿鍐?
        Args:
            min_salary: 鏈€浣庤柂璧?            max_salary: 鏈€楂樿柂璧?
        Returns:
            bool: 钖祫鏄惁鍦ㄨ寖鍥村唴
        """
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
    tracker_advices = relationship(
        "TrackerAdvice",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        Index('idx_application_user_status', 'user_id', 'status'),
        Index('idx_application_job_status', 'job_id', 'status'),
        Index('idx_application_date_status', 'application_date', 'status'),
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
