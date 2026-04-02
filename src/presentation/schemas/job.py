"""Job-related Pydantic models."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobBase(BaseModel):
    """Base job model."""

    title: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    description: Optional[str]
    requirements: Optional[str]


class JobCreate(JobBase):
    """Job create request model."""

    salary: Optional[str]
    work_type: Optional[str]
    experience: Optional[str]
    education: Optional[str]
    welfare: Optional[str]
    tags: Optional[str]
    source: str
    source_url: Optional[str]
    source_id: Optional[str]


class JobUpdate(JobBase):
    """Job update request model."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary: Optional[str] = None
    work_type: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    welfare: Optional[str] = None
    tags: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_id: Optional[str] = None
    is_active: Optional[bool] = None


class Job(JobBase):
    """Job response model."""

    id: int
    company_logo: Optional[str]
    salary: Optional[str]
    work_type: Optional[str]
    experience: Optional[str]
    education: Optional[str]
    welfare: Optional[str]
    tags: Optional[str]
    source: str
    source_url: Optional[str]
    source_id: Optional[str]
    is_active: bool
    publish_date: Optional[datetime]
    deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobApplicationBase(BaseModel):
    """Job application base model."""

    job_id: int
    resume_id: int
    notes: Optional[str] = Field(None, max_length=500)


class JobApplicationCreate(JobApplicationBase):
    """Job application create request model."""

    pass


class JobApplicationUpdate(BaseModel):
    """Job application update request model."""

    status: Optional[str] = Field(None, min_length=1, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)


class JobApplication(JobApplicationBase):
    """Job application response model."""

    id: int
    user_id: int
    application_date: datetime
    status: str
    status_updated_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobMatchRequest(BaseModel):
    """Job match request model."""

    resume_id: int = Field(..., ge=1)


class JobMatchResponse(BaseModel):
    """Job match response model."""

    mode: Literal["job_match"]
    job_id: int
    resume_id: int
    score: int = Field(..., ge=0, le=100)
    feedback: str
    raw_content: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class JobMatchRecord(BaseModel):
    """Persisted job match record model."""

    id: int
    job_id: int
    resume_id: int
    mode: Literal["job_match"]
    score: int = Field(..., ge=0, le=100)
    feedback: str
    raw_content: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
