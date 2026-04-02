"""
闈㈣瘯鐩稿叧鐨凱ydantic妯″瀷
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class InterviewQuestionBase(BaseModel):
    """闈㈣瘯闂鍩虹妯″瀷"""

    question_type: str = Field(..., min_length=1, max_length=50)
    difficulty: Optional[str] = Field(None, min_length=1, max_length=20)
    question_text: str
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=255)
    sample_answer: Optional[str] = None
    reference_material: Optional[str] = Field(None, max_length=255)


class InterviewQuestionCreate(InterviewQuestionBase):
    """鍒涘缓闈㈣瘯闂璇锋眰妯″瀷"""

    pass


class InterviewQuestionUpdate(BaseModel):
    """鏇存柊闈㈣瘯闂璇锋眰妯″瀷"""

    question_type: Optional[str] = Field(None, min_length=1, max_length=50)
    difficulty: Optional[str] = Field(None, min_length=1, max_length=20)
    question_text: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=255)
    sample_answer: Optional[str] = None
    reference_material: Optional[str] = Field(None, max_length=255)


class InterviewQuestion(InterviewQuestionBase):
    """闈㈣瘯闂鍝嶅簲妯″瀷"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewRecordBase(BaseModel):
    """闈㈣瘯璁板綍鍩虹妯″瀷"""

    job_id: Optional[int] = None
    question_id: int
    user_answer: str
    ai_evaluation: Optional[str] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    feedback: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class InterviewRecordCreate(InterviewRecordBase):
    """鍒涘缓闈㈣瘯璁板綍璇锋眰妯″瀷"""

    pass


class InterviewRecordUpdate(BaseModel):
    """鏇存柊闈㈣瘯璁板綍璇锋眰妯″瀷"""

    job_id: Optional[int] = None
    question_id: Optional[int] = None
    user_answer: Optional[str] = None
    ai_evaluation: Optional[str] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    feedback: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class InterviewRecord(InterviewRecordBase):
    """闈㈣瘯璁板綍鍝嶅簲妯″瀷"""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewSessionBase(BaseModel):
    """闈㈣瘯浼氳瘽鍩虹妯″瀷"""

    job_id: Optional[int] = None
    session_type: str = Field(default="technical", max_length=50)
    duration: Optional[int] = None
    total_questions: Optional[int] = None
    average_score: Optional[float] = None
    completed: Optional[int] = Field(default=0, ge=0, le=1)


class InterviewSessionCreate(InterviewSessionBase):
    """鍒涘缓闈㈣瘯浼氳瘽璇锋眰妯″瀷"""

    pass


class InterviewSessionUpdate(BaseModel):
    """鏇存柊闈㈣瘯浼氳瘽璇锋眰妯″瀷"""

    job_id: Optional[int] = None
    session_type: Optional[str] = Field(None, max_length=50)
    duration: Optional[int] = None
    total_questions: Optional[int] = None
    average_score: Optional[float] = None
    completed: Optional[int] = Field(None, ge=0, le=1)


class InterviewSession(InterviewSessionBase):
    """闈㈣瘯浼氳瘽鍝嶅簲妯″瀷"""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewQuestionGenerationRequest(BaseModel):
    """Request model for generated interview questions."""

    job_context: str = Field(..., min_length=1)
    resume_id: Optional[int] = Field(default=None, ge=1)
    count: int = Field(default=5, ge=1, le=20)


class GeneratedInterviewQuestion(BaseModel):
    """Generated interview question item."""

    question_number: int = Field(..., ge=1)
    question_text: str
    question_type: str
    difficulty: str
    category: str


class InterviewQuestionGenerationResponse(BaseModel):
    """Response model for generated interview questions."""

    mode: Literal["question_generation"]
    job_context: str
    resume_context: Optional[str]
    count: int
    questions: list[GeneratedInterviewQuestion]
    raw_content: str
    provider: Optional[str] = None
    model: Optional[str] = None


class InterviewAnswerEvaluationRequest(BaseModel):
    """Request model for answer evaluation."""

    question_text: str = Field(..., min_length=1)
    user_answer: str = Field(..., min_length=1)
    job_context: Optional[str] = None


class InterviewAnswerEvaluationResponse(BaseModel):
    """Response model for answer evaluation."""

    mode: Literal["answer_evaluation"]
    question_text: str
    user_answer: str
    job_context: Optional[str]
    score: int = Field(..., ge=0, le=100)
    feedback: str
    raw_content: str
    provider: Optional[str] = None
    model: Optional[str] = None


class InterviewRecordEvaluationRequest(BaseModel):
    """Request model for persisted record evaluation."""

    job_context: Optional[str] = None


class InterviewRecordEvaluationResponse(BaseModel):
    """Response model for persisted record evaluation."""

    mode: Literal["answer_evaluation"]
    record_id: int
    score: int = Field(..., ge=0, le=100)
    feedback: str
    ai_evaluation: str
    raw_content: str
    provider: Optional[str] = None
    model: Optional[str] = None
    answered_at: datetime
