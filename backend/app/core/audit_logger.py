"""
Structured audit logging system.

Every sensitive action in the system emits a structured AuditEntry.
Entries are written to both an in-memory buffer (for real-time API queries)
and an append-only JSONL file on disk (for persistence across restarts).

Privacy principles applied:
- Email body content is NEVER logged — only metadata (message_id, subject if
  needed for clarity, sender domain).
- Voice transcripts are NOT stored — only the classified intent is logged.
- Audio bytes are never written to disk by any component.
- IP addresses are logged for security analysis but should be redacted before
  sharing logs externally.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    # Authentication
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"

    # Email
    EMAIL_READ = "email.read"
    EMAIL_SUMMARISE = "email.summarise"
    EMAIL_SEND = "email.send"
    EMAIL_DRAFT = "email.draft"
    EMAIL_SEND_FAILED = "email.send_failed"

    # Calendar
    CALENDAR_READ = "calendar.read"
    CALENDAR_READ_EMPLOYEE = "calendar.read_employee"
    CALENDAR_EVENT_CREATED = "calendar.event_created"
    CALENDAR_EVENT_UPDATED = "calendar.event_updated"
    CALENDAR_EVENT_DELETED = "calendar.event_deleted"
    CALENDAR_AVAILABILITY_CHECK = "calendar.availability_check"

    # Voice / Intent
    VOICE_COMMAND = "voice.command"
    INTENT_CLASSIFIED = "intent.classified"

    # Access control
    PERMISSION_DENIED = "permission.denied"

    # Admin
    ADMIN_ACCESS = "admin.access"
    USER_ROLE_CHANGED = "user.role_changed"


class AuditEntry(BaseModel):
    """Immutable audit log record."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: str
    actor_email: str
    actor_role: str = "unknown"
    action: AuditAction
    target_resource: str = ""
    outcome: str = "success"  # "success" | "failure" | "denied"
    detail: dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ip_address: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


class AuditLogger:
    """Thread-safe audit logger with in-memory buffer and JSONL file backend."""

    _MAX_MEMORY_ENTRIES = 1000

    def __init__(self, log_file: str = "./logs/audit.jsonl") -> None:
        self._entries: list[AuditEntry] = []
        self._lock = asyncio.Lock()
        self._log_path = Path(log_file)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    async def log(
        self,
        action: AuditAction,
        actor_id: str,
        actor_email: str,
        *,
        actor_role: str = "unknown",
        target_resource: str = "",
        outcome: str = "success",
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
        ip_address: str = "",
    ) -> AuditEntry:
        """Create and persist an AuditEntry."""
        entry = AuditEntry(
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            action=action,
            target_resource=target_resource,
            outcome=outcome,
            detail=details or {},
            request_id=request_id or str(uuid.uuid4()),
            ip_address=ip_address,
        )

        async with self._lock:
            self._entries.append(entry)
            # Trim memory buffer
            if len(self._entries) > self._MAX_MEMORY_ENTRIES:
                self._entries = self._entries[-self._MAX_MEMORY_ENTRIES :]
            # Append to JSONL file
            self._append_to_file(entry)

        return entry

    def _append_to_file(self, entry: AuditEntry) -> None:
        """Synchronously append entry to JSONL file (called under lock)."""
        try:
            with self._log_path.open("a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except OSError:
            pass  # Never let logging failure crash the application

    async def query(
        self,
        query: "AuditLogQuery",  # forward ref
    ) -> "AuditLogResponse":
        """Query the in-memory buffer with optional filters."""
        from app.schemas.audit import AuditLogQuery, AuditLogResponse  # lazy import

        async with self._lock:
            results = list(self._entries)

        if query.action_filter:
            results = [
                e for e in results if query.action_filter.lower() in e.action.value.lower()
            ]
        if query.actor_filter:
            af = query.actor_filter.lower()
            results = [
                e
                for e in results
                if af in e.actor_email.lower() or af in e.actor_id.lower()
            ]
        if query.since:
            results = [e for e in results if e.timestamp >= query.since]
        if query.until:
            results = [e for e in results if e.timestamp <= query.until]

        total = len(results)
        # Most recent first
        results.sort(key=lambda e: e.timestamp, reverse=True)
        page = results[query.offset : query.offset + query.limit]

        return AuditLogResponse(entries=page, total=total)

    async def get_recent(self, limit: int = 20) -> list[AuditEntry]:
        async with self._lock:
            return list(reversed(self._entries[-limit:]))


_audit_logger_instance: AuditLogger | None = None


@lru_cache(maxsize=1)
def get_audit_logger() -> AuditLogger:
    """Return the singleton AuditLogger instance."""
    log_file = os.getenv("AUDIT_LOG_FILE", "./logs/audit.jsonl")
    return AuditLogger(log_file=log_file)
