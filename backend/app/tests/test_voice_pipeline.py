"""
Tests for the voice command pipeline — scheduling, confirmation, and calendar update.

Covers:
- Meeting creation end-to-end (command → confirm → event in calendar)
- Correct date resolution for all weekdays after confirmation
- Correct time resolution including "at X" bare format
- Meeting not created when confirmation is declined
- Expired action token returns error gracefully
- Clarification returned when required entities missing
- Email scoping (Alex and Jamie see different inboxes)
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from app.intents.models import Intent
from app.integrations.graph.mock_adapter import MockGraphCalendarAdapter, MockGraphMailAdapter
from app.services.calendar_service import CalendarService
from app.services.email_service import EmailService
from app.services.voice_service import VoiceService, _PENDING_ACTIONS
from app.schemas.voice import VoiceCommandRequest, ConfirmationRequest
from app.intents.classifier import HybridIntentClassifier
from app.intents.rules_engine import RulesClassifier


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ALEX_EMAIL = "a.morgan@contoso.com"
JAMIE_EMAIL = "jamie.lee@dev.local"

ALEX_CONTEXT = {
    "sub": "alex-sub-001",
    "email": ALEX_EMAIL,
    "role": "manager",
    "graph_access_token": "mock",
}

JAMIE_CONTEXT = {
    "sub": "jamie-sub-001",
    "email": JAMIE_EMAIL,
    "role": "employee",
    "graph_access_token": "mock",
}


class _SilentTTS:
    async def synthesise(self, text: str) -> bytes:
        return b""


@pytest.fixture
def calendar_adapter():
    return MockGraphCalendarAdapter()


@pytest.fixture
def mail_adapter():
    return MockGraphMailAdapter()


@pytest.fixture
def voice_service(calendar_adapter, mail_adapter):
    classifier = HybridIntentClassifier(rules=RulesClassifier(), llm_parser=None)
    cal_service = CalendarService(calendar_adapter=calendar_adapter)
    email_service = EmailService(mail_adapter=mail_adapter)
    return VoiceService(
        stt_provider=None,
        tts_provider=_SilentTTS(),
        classifier=classifier,
        email_service=email_service,
        calendar_service=cal_service,
    )


# ---------------------------------------------------------------------------
# Meeting creation — full flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestMeetingCreationFlow:

    async def test_create_meeting_goes_to_confirmation(self, voice_service):
        req = VoiceCommandRequest(transcript="Schedule a meeting with Jamie tomorrow at 2 PM")
        result = await voice_service.process_command(req, ALEX_CONTEXT)
        assert result.requires_confirmation is True
        assert result.action_id is not None
        assert result.intent == Intent.CREATE_MEETING.value

    async def test_confirm_creates_event(self, voice_service, calendar_adapter):
        # Step 1: issue command
        req = VoiceCommandRequest(transcript="Schedule a meeting with Jamie tomorrow at 2 PM")
        cmd_result = await voice_service.process_command(req, ALEX_CONTEXT)
        assert cmd_result.requires_confirmation

        # Step 2: confirm
        confirm_req = ConfirmationRequest(action_id=cmd_result.action_id, confirmed=True)
        confirm_result = await voice_service.confirm_action(confirm_req, ALEX_CONTEXT)
        assert confirm_result.requires_confirmation is False
        assert "event" in (confirm_result.action_result or {})

        # Step 3: verify event appears in Alex's calendar
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=14)
        events = await calendar_adapter.get_events(ALEX_EMAIL, start, end)
        subjects = [e["subject"] for e in events]
        assert any("Jamie" in s or "Meeting" in s for s in subjects), (
            f"Created meeting not found. Events: {subjects}"
        )

    async def test_decline_does_not_create_event(self, voice_service, calendar_adapter):
        req = VoiceCommandRequest(transcript="Schedule a meeting with Jamie tomorrow at 3 PM")
        cmd_result = await voice_service.process_command(req, ALEX_CONTEXT)
        assert cmd_result.requires_confirmation

        before = await calendar_adapter.get_events(
            ALEX_EMAIL,
            datetime.now(timezone.utc),
            datetime.now(timezone.utc) + timedelta(days=14),
        )
        before_count = len(before)

        confirm_req = ConfirmationRequest(action_id=cmd_result.action_id, confirmed=False)
        cancel_result = await voice_service.confirm_action(confirm_req, ALEX_CONTEXT)
        assert "cancelled" in cancel_result.response_text.lower() or "cancel" in cancel_result.response_text.lower()

        after = await calendar_adapter.get_events(
            ALEX_EMAIL,
            datetime.now(timezone.utc),
            datetime.now(timezone.utc) + timedelta(days=14),
        )
        assert len(after) == before_count, "Event count changed after cancellation"

    async def test_expired_action_returns_error(self, voice_service):
        req = VoiceCommandRequest(transcript="Schedule a meeting with Jamie tomorrow at 2 PM")
        cmd_result = await voice_service.process_command(req, ALEX_CONTEXT)
        action_id = cmd_result.action_id

        # Force-expire the action
        _PENDING_ACTIONS[action_id]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)

        confirm_req = ConfirmationRequest(action_id=action_id, confirmed=True)
        expired_result = await voice_service.confirm_action(confirm_req, ALEX_CONTEXT)
        assert "timed out" in expired_result.response_text.lower() or "expired" in expired_result.response_text.lower()

    async def test_missing_date_and_time_asks_clarification(self, voice_service):
        req = VoiceCommandRequest(transcript="Schedule a meeting with Jamie")
        result = await voice_service.process_command(req, ALEX_CONTEXT)
        assert result.clarification_needed is True
        assert result.requires_confirmation is False


# ---------------------------------------------------------------------------
# Date resolution per weekday
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestMeetingDateResolution:
    """Confirm the resolved event date matches the weekday spoken."""

    async def _get_event_date(self, voice_service, calendar_adapter, command: str) -> str | None:
        req = VoiceCommandRequest(transcript=command)
        cmd_result = await voice_service.process_command(req, ALEX_CONTEXT)
        if not cmd_result.requires_confirmation:
            return None
        confirm_req = ConfirmationRequest(action_id=cmd_result.action_id, confirmed=True)
        confirm_result = await voice_service.confirm_action(confirm_req, ALEX_CONTEXT)
        event = (confirm_result.action_result or {}).get("event", {})
        return event.get("start", "")

    @staticmethod
    def _expected_date(weekday_offset: int) -> str:
        from datetime import date
        today = date.today()
        days = (weekday_offset - today.weekday()) % 7 or 7
        return (today + timedelta(days=days)).strftime("%Y-%m-%d")

    async def test_monday(self, voice_service, calendar_adapter):
        start = await self._get_event_date(voice_service, calendar_adapter,
                                           "Schedule a meeting with Jamie on Monday at 10 AM")
        assert start is not None and self._expected_date(0) in start

    async def test_tuesday(self, voice_service, calendar_adapter):
        start = await self._get_event_date(voice_service, calendar_adapter,
                                           "Schedule a meeting with Jamie on Tuesday at 2 PM")
        assert start is not None and self._expected_date(1) in start

    async def test_wednesday(self, voice_service, calendar_adapter):
        start = await self._get_event_date(voice_service, calendar_adapter,
                                           "Book a sync with Sarah on Wednesday at 11 AM")
        assert start is not None and self._expected_date(2) in start

    async def test_thursday(self, voice_service, calendar_adapter):
        start = await self._get_event_date(voice_service, calendar_adapter,
                                           "Set up a kickoff with Omar on Thursday at 3 PM")
        assert start is not None and self._expected_date(3) in start

    async def test_friday(self, voice_service, calendar_adapter):
        start = await self._get_event_date(voice_service, calendar_adapter,
                                           "Schedule a call with Ali on Friday at 9 AM")
        assert start is not None and self._expected_date(4) in start

    async def test_time_parsed_from_bare_at_11(self, voice_service, calendar_adapter):
        start = await self._get_event_date(voice_service, calendar_adapter,
                                           "Schedule a meeting with Jamie on Thursday at 11")
        assert start is not None
        # Time should be 11:00, not 09:00 default
        assert "T11:00" in start, f"Expected 11:00 in start time, got: {start}"

    async def test_time_parsed_from_bare_at_3(self, voice_service, calendar_adapter):
        start = await self._get_event_date(voice_service, calendar_adapter,
                                           "Book a check-in with Ali on Monday at 3")
        assert start is not None
        # "3" is ambiguous 1-6 → assumes PM = 15:00
        assert "T15:00" in start, f"Expected 15:00 in start time, got: {start}"


# ---------------------------------------------------------------------------
# Email separation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestEmailSeparation:

    async def test_alex_inbox_is_manager(self, voice_service):
        req = VoiceCommandRequest(transcript="Read my emails")
        result = await voice_service.process_command(req, ALEX_CONTEXT)
        messages = (result.action_result or {}).get("messages", [])
        assert len(messages) > 0
        subjects = [m.get("subject", "") for m in messages]
        # Alex gets manager emails (financial, strategic)
        assert any("Q3" in s or "Board" in s or "Acme" in s or "Invoice" in s for s in subjects), (
            f"Alex's inbox doesn't look like manager mail. Subjects: {subjects}"
        )

    async def test_jamie_inbox_is_employee(self, voice_service):
        req = VoiceCommandRequest(transcript="Read my emails")
        result = await voice_service.process_command(req, JAMIE_CONTEXT)
        messages = (result.action_result or {}).get("messages", [])
        assert len(messages) > 0
        subjects = [m.get("subject", "") for m in messages]
        # Jamie gets employee emails (sprint tasks, HR, peer review)
        assert any("Sprint" in s or "HR" in s or "Peer" in s or "Security" in s or "Holiday" in s
                   for s in subjects), (
            f"Jamie's inbox doesn't look like employee mail. Subjects: {subjects}"
        )

    async def test_alex_and_jamie_inboxes_differ(self, voice_service):
        alex_req = VoiceCommandRequest(transcript="Read my emails")
        jamie_req = VoiceCommandRequest(transcript="Read my emails")

        alex_result = await voice_service.process_command(alex_req, ALEX_CONTEXT)
        jamie_result = await voice_service.process_command(jamie_req, JAMIE_CONTEXT)

        alex_subjects = {m["subject"] for m in (alex_result.action_result or {}).get("messages", [])}
        jamie_subjects = {m["subject"] for m in (jamie_result.action_result or {}).get("messages", [])}

        assert alex_subjects != jamie_subjects, (
            "Alex and Jamie have identical inboxes — email separation is broken"
        )
