"""Pydantic v2 schemas for audit log endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.core.audit_logger import AuditEntry


class AuditLogQuery(BaseModel):
    limit: int = 50
    offset: int = 0
    action_filter: str | None = None
    actor_filter: str | None = None
    since: datetime | None = None
    until: datetime | None = None


class AuditLogResponse(BaseModel):
    entries: list[AuditEntry]
    total: int
