"""
Tracker-related Pydantic models.
"""

import json
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApplicationTrackerBase(BaseModel):
    """Base job application tracker model."""

    job_id: int
    resume_id: int
    status: str = Field(default="applied", max_length=50)
    notes: Optional[str] = Field(None, max_length=500)


class ApplicationTrackerCreate(ApplicationTrackerBase):
    """Create request model for a job application."""


class ApplicationTrackerUpdate(BaseModel):
    """Update request model for a job application."""

    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)


class ApplicationTracker(ApplicationTrackerBase):
    """Job application response model."""

    id: int
    user_id: int
    application_date: datetime
    status_updated_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationAdviceResponse(BaseModel):
    """Application advice response model."""

    mode: Literal["tracker_advice"]
    application_id: int
    summary: str
    next_steps: list[str]
    risks: list[str]
    raw_content: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TrackerAdviceRecord(BaseModel):
    """Persisted tracker advice response model."""

    id: int
    application_id: int
    mode: Literal["tracker_advice"]
    summary: str
    next_steps: list[str]
    risks: list[str]
    raw_content: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("next_steps", "risks", mode="before")
    @classmethod
    def _parse_json_list(cls, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return []
            return parsed if isinstance(parsed, list) else []
        return value
