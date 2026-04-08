"""UserLlmConfig Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserLlmConfigBase(BaseModel):
    """Shared field definitions."""

    agent: str = Field(..., description="Agent identifier: resume_agent / job_agent / interview_agent")
    provider: str = Field(..., description="Provider identifier")
    model: str = Field(..., description="Model name")
    base_url: Optional[str] = Field(None, description="Custom API endpoint")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Generation temperature 0-2")


class UserLlmConfigCreate(UserLlmConfigBase):
    """Schema for creating/updating config (includes plaintext api_key)."""

    api_key: str = Field(..., description="API Key (plaintext, encrypted in transit)")


class UserLlmConfigResponse(UserLlmConfigBase):
    """Schema returned to frontend (excludes api_key)."""

    is_active: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
