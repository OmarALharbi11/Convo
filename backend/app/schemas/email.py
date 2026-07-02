"""Pydantic v2 schemas for email endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class EmailMessage(BaseModel):
    id: str
    subject: str
    sender_name: str
    sender_email: str
    received_at: datetime
    is_read: bool
    preview: str
    body_text: str | None = None
    importance: Literal["high", "normal", "low"] = "normal"


class EmailListResponse(BaseModel):
    messages: list[EmailMessage]
    total: int
    has_more: bool
    fetched_at: datetime


class EmailFilter(BaseModel):
    folder: str = "inbox"
    only_unread: bool = False
    limit: int = 10
    from_address: str | None = None
    subject_contains: str | None = None
    since_date: datetime | None = None


class SendEmailRequest(BaseModel):
    to: list[str]
    subject: str
    body: str
    cc: list[str] = []
    is_draft: bool = False

    @field_validator("to")
    @classmethod
    def recipients_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one recipient is required.")
        return v

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Email subject cannot be empty.")
        return v

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Email body cannot be empty.")
        return v


class SendEmailResponse(BaseModel):
    message_id: str
    status: str  # "sent" | "draft"
    sent_at: datetime


class EmailSummary(BaseModel):
    message_id: str
    subject: str
    sender_email: str
    key_points: list[str]
    sentiment: Literal["positive", "negative", "neutral"]
    urgency_level: Literal["high", "medium", "low"]
    summary_text: str
