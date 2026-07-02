"""
Email service — business logic layer between routes and Graph adapter.

Responsibilities:
- Map raw Graph dicts → typed Pydantic schemas
- Implement email summarisation (extractive, no LLM required)
- Validate business rules before delegating to the adapter
- Never expose raw Graph data to routes
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.schemas.email import (
    EmailFilter,
    EmailListResponse,
    EmailMessage,
    EmailSummary,
    SendEmailRequest,
    SendEmailResponse,
)

# Simple word lists for urgency and sentiment detection
_URGENCY_HIGH = {"urgent", "asap", "critical", "immediately", "escalation", "p1", "priority", "action required"}
_URGENCY_MEDIUM = {"soon", "important", "needed", "please review", "follow up", "reminder"}
_POSITIVE_WORDS = {"thank", "great", "good", "well done", "approved", "confirmed", "success", "congratulations"}
_NEGATIVE_WORDS = {"issue", "problem", "error", "fail", "concern", "risk", "delay", "blocked", "escalat"}


class EmailService:
    def __init__(self, mail_adapter) -> None:
        self._adapter = mail_adapter

    async def get_inbox(self, user_email: str, email_filter: EmailFilter) -> EmailListResponse:
        raw_messages = await self._adapter.get_messages(
            user_email=user_email,
            folder=email_filter.folder,
            limit=email_filter.limit,
            only_unread=email_filter.only_unread,
            from_address=email_filter.from_address,
            subject_contains=email_filter.subject_contains,
            since_date=email_filter.since_date,
        )
        messages = [self._map_message(m) for m in raw_messages]
        return EmailListResponse(
            messages=messages,
            total=len(messages),
            has_more=len(messages) == email_filter.limit,
            fetched_at=datetime.now(timezone.utc),
        )

    async def get_message(self, user_email: str, message_id: str) -> EmailMessage:
        raw = await self._adapter.get_message_by_id(message_id)
        return self._map_message(raw)

    async def summarise_message(self, user_email: str, message_id: str) -> EmailSummary:
        raw = await self._adapter.get_message_by_id(message_id)
        msg = self._map_message(raw)
        return self._summarise(msg)

    async def summarise_recent(self, user_email: str, count: int = 5) -> list[EmailSummary]:
        raw_messages = await self._adapter.get_messages(
            user_email=user_email,
            folder="inbox",
            limit=count,
        )
        messages = [self._map_message(m) for m in raw_messages]
        return [self._summarise(m) for m in messages]

    async def send_email(self, sender_email: str, request: SendEmailRequest) -> SendEmailResponse:
        message_id = await self._adapter.send_message(
            sender_email=sender_email,
            to_recipients=request.to,
            subject=request.subject,
            body=request.body,
            cc_recipients=request.cc or [],
        )
        return SendEmailResponse(
            message_id=message_id,
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )

    async def create_draft(self, sender_email: str, request: SendEmailRequest) -> SendEmailResponse:
        draft_id = await self._adapter.create_draft(
            sender_email=sender_email,
            to_recipients=request.to,
            subject=request.subject,
            body=request.body,
        )
        return SendEmailResponse(
            message_id=draft_id,
            status="draft",
            sent_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_message(raw: dict[str, Any]) -> EmailMessage:
        """Map a raw adapter dict to a typed EmailMessage schema."""
        received_at = raw.get("received_at")
        if isinstance(received_at, str):
            received_at = datetime.fromisoformat(received_at)
        elif not isinstance(received_at, datetime):
            received_at = datetime.now(timezone.utc)

        return EmailMessage(
            id=str(raw.get("id", "")),
            subject=str(raw.get("subject", "(No Subject)")),
            sender_name=str(raw.get("sender_name", "")),
            sender_email=str(raw.get("sender_email", "")),
            received_at=received_at,
            is_read=bool(raw.get("is_read", True)),
            preview=str(raw.get("preview", ""))[:200],
            body_text=raw.get("body_text"),
            importance=raw.get("importance", "normal"),
        )

    def _summarise(self, msg: EmailMessage) -> EmailSummary:
        """Extractive summarisation — no LLM required."""
        text = msg.body_text or msg.preview
        text_lower = text.lower()
        subject_lower = msg.subject.lower()
        combined = text_lower + " " + subject_lower

        # Urgency detection
        if any(w in combined for w in _URGENCY_HIGH):
            urgency = "high"
        elif any(w in combined for w in _URGENCY_MEDIUM):
            urgency = "medium"
        else:
            urgency = "low"

        # Sentiment detection
        pos_count = sum(1 for w in _POSITIVE_WORDS if w in combined)
        neg_count = sum(1 for w in _NEGATIVE_WORDS if w in combined)
        if neg_count > pos_count:
            sentiment = "negative"
        elif pos_count > neg_count:
            sentiment = "positive"
        else:
            sentiment = "neutral"

        # Extract key points — first 2 sentences + subject keywords
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        key_points = sentences[:2]
        if not key_points:
            key_points = [msg.preview[:100]]

        # Summary text — one short sentence
        first = sentences[0] if sentences else msg.preview
        summary_text = first[:120] + ("…" if len(first) > 120 else "")

        return EmailSummary(
            message_id=msg.id,
            subject=msg.subject,
            sender_email=msg.sender_email,
            key_points=key_points,
            sentiment=sentiment,
            urgency_level=urgency,
            summary_text=summary_text,
        )
