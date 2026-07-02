"""Pydantic v2 schemas for authentication endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr

from app.core.rbac import UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserInfo(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: UserRole
    permissions: list[str]
