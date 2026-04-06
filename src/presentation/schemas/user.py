"""Pydantic schemas for user APIs."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user payload."""

    username: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)


class UserCreate(UserBase):
    """User creation payload."""

    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """User update payload."""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)


class User(UserBase):
    """User response payload."""

    id: int
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """User login payload."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Bearer token response payload."""

    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login request payload."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response with access token.

    Refresh token is stored in HttpOnly cookie.
    """

    access_token: str
    token_type: str = "bearer"


class TokenRefreshResponse(BaseModel):
    """Refresh token exchange response with new access token."""

    access_token: str
    token_type: str = "bearer"


class UserProfileBase(BaseModel):
    """Base user profile payload."""

    education: Optional[str] = Field(None, max_length=500)
    work_experience: Optional[str] = Field(None, max_length=1000)
    skills: Optional[str] = Field(None, max_length=500)
    preferences: Optional[str] = Field(None, max_length=500)
    job_target: Optional[str] = Field(None, max_length=200)


class UserProfileCreate(UserProfileBase):
    """User profile creation payload."""

    pass


class UserProfileUpdate(UserProfileBase):
    """User profile update payload."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
