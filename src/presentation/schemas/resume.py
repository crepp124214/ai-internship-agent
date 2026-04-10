"""
Resume-related Pydantic models.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):
    """Base resume model."""

    title: str = Field(..., min_length=1, max_length=200)


class ResumeCreate(ResumeBase):
    """Resume create request model."""

    file_path: str


class ResumeUpdate(BaseModel):
    """Resume update request model."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    original_file_path: Optional[str] = Field(default=None, max_length=500)
    file_name: Optional[str] = Field(default=None, max_length=255)
    file_type: Optional[str] = Field(default=None, max_length=20)
    file_size: Optional[int] = Field(default=None, ge=0)
    processed_content: Optional[str] = None
    resume_text: Optional[str] = None
    language: Optional[str] = Field(default=None, max_length=20)
    is_default: Optional[bool] = None


class Resume(ResumeBase):
    """Resume response model."""

    id: int
    user_id: int
    original_file_path: str
    file_name: str
    file_type: str
    file_size: Optional[int]
    processed_content: Optional[str]
    resume_text: Optional[str]
    language: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeAnalysisRequest(BaseModel):
    """Resume analysis request model."""

    target_role: Optional[str] = Field(default=None, max_length=200)


class ResumeAnalysisResponse(BaseModel):
    """Resume analysis response model."""

    mode: Literal["summary", "improvements"]
    resume_id: int
    target_role: Optional[str]
    content: str
    raw_content: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = Field(default="success", description="执行状态: success | fallback | error")
    fallback_used: Optional[bool] = Field(default=False, description="是否使用了 fallback")


class ResumeOptimizationBase(BaseModel):
    """Base resume optimization model."""

    original_text: str
    optimized_text: str
    optimization_type: str = Field(..., min_length=1, max_length=50)
    keywords: Optional[str] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    ai_suggestion: Optional[str] = None
    mode: Literal["resume_summary", "resume_improvements"] = "resume_improvements"
    raw_content: str
    provider: str
    model: str
    status: str = Field(..., min_length=1, max_length=50)
    fallback_used: bool = False


class ResumeOptimizationCreate(ResumeOptimizationBase):
    """Resume optimization create request model."""

    resume_id: int


class ResumeOptimization(ResumeOptimizationBase):
    """Resume optimization response model."""

    id: int
    resume_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
