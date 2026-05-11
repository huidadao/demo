"""Pydantic schemas for user authentication."""

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (excludes password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Schema for generic message response."""

    message: str


class UserUpdate(BaseModel):
    """Schema for user profile update."""

    email: Optional[EmailStr] = None


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr


class ChangePasswordRequest(BaseModel):
    """Schema for password change request."""

    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False
