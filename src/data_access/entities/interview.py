"""Interview persistence entities."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from src.data_access.database import Base


class InterviewQuestion(Base):
    """Interview question bank entry."""

    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True, comment="Question ID")
    question_type = Column(String(50), nullable=False, index=True, comment="Question type")
    difficulty = Column(String(20), index=True, comment="Difficulty level")
    question_text = Column(Text, nullable=False, comment="Question text")
    category = Column(String(100), index=True, comment="Question category")
    tags = Column(String(500), comment="Comma-separated tags")
    sample_answer = Column(Text, comment="Sample answer")
    reference_material = Column(String(500), comment="Reference material")
    is_active = Column(Boolean, default=True, index=True, comment="Whether the question is active")
    created_at = Column(DateTime, default=datetime.now, index=True, comment="Created at")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="Updated at")

    interview_records = relationship("InterviewRecord", back_populates="question", lazy="dynamic")

    __table_args__ = (
        Index("idx_question_type_difficulty", "question_type", "difficulty"),
        Index("idx_question_category_type", "category", "question_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<InterviewQuestion(id={self.id}, type='{self.question_type}', "
            f"difficulty='{self.difficulty}')>"
        )


class InterviewRecord(Base):
    """Interview answer record with inline AI evaluation."""

    __tablename__ = "interview_records"

    id = Column(Integer, primary_key=True, index=True, comment="Record ID")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID",
    )
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="SET NULL"),
        index=True,
        comment="Related job ID",
    )
    question_id = Column(
        Integer,
        ForeignKey("interview_questions.id", ondelete="SET NULL"),
        index=True,
        comment="Related question ID",
    )

    user_answer = Column(Text, comment="User answer")
    ai_evaluation = Column(Text, comment="Raw AI evaluation content")
    score = Column(Integer, index=True, comment="Evaluation score 0-100")
    feedback = Column(Text, comment="Evaluation feedback")
    provider = Column(String(50), index=True, comment="LLM provider")
    model = Column(String(100), index=True, comment="LLM model")

    answered_at = Column(DateTime, index=True, comment="Answered at")
    created_at = Column(DateTime, default=datetime.now, comment="Created at")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="Updated at")

    user = relationship("User", back_populates="interview_records", lazy="joined")
    job = relationship("Job", back_populates="interview_records", lazy="joined")
    question = relationship("InterviewQuestion", back_populates="interview_records", lazy="joined")

    __table_args__ = (
        Index("idx_record_user_question", "user_id", "question_id"),
        Index("idx_record_user_score", "user_id", "score"),
        Index("idx_record_job_score", "job_id", "score"),
    )

    def validate_score(self) -> None:
        if self.score is not None and (self.score < 0 or self.score > 100):
            raise ValueError(f"score must be within 0-100, got {self.score}")

    def __repr__(self) -> str:
        return (
            f"<InterviewRecord(id={self.id}, user_id={self.user_id}, "
            f"question_id={self.question_id}, score={self.score})>"
        )


class InterviewSession(Base):
    """Interview practice session."""

    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True, comment="Session ID")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID",
    )
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="SET NULL"),
        index=True,
        comment="Related job ID",
    )

    session_type = Column(String(50), default="technical", index=True, comment="Session type")
    duration = Column(Integer, comment="Duration in minutes")
    total_questions = Column(Integer, comment="Total question count")
    answered_questions = Column(Integer, default=0, comment="Answered question count")
    average_score = Column(Float, index=True, comment="Average score")
    completed = Column(Boolean, default=False, index=True, comment="Whether the session is completed")

    started_at = Column(DateTime, index=True, comment="Started at")
    completed_at = Column(DateTime, comment="Completed at")
    created_at = Column(DateTime, default=datetime.now, index=True, comment="Created at")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="Updated at")

    user = relationship("User", back_populates="interview_sessions", lazy="joined")
    job = relationship("Job", back_populates="interview_sessions", lazy="joined")

    __table_args__ = (
        Index("idx_session_user_completed", "user_id", "completed"),
        Index("idx_session_user_type", "user_id", "session_type"),
        Index("idx_session_job_completed", "job_id", "completed"),
    )

    def validate_average_score(self) -> None:
        if self.average_score is not None and (self.average_score < 0 or self.average_score > 100):
            raise ValueError(f"average_score must be within 0-100, got {self.average_score}")

    def __repr__(self) -> str:
        return (
            f"<InterviewSession(id={self.id}, user_id={self.user_id}, "
            f"type='{self.session_type}', completed={self.completed})>"
        )

    def get_progress_percentage(self) -> float:
        if self.total_questions is None or self.total_questions == 0:
            return 0.0
        return (self.answered_questions / self.total_questions) * 100

    def is_in_progress(self) -> bool:
        return not self.completed and self.total_questions is not None

    def is_completed(self) -> bool:
        return self.completed
