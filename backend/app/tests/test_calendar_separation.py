"""
Tests for calendar data separation between users.

Covers:
- Alex (manager) and Jamie (employee) see different personal events
- Shared events appear for both
- Admin sees everything
- Voice-created events appear for the correct owner
- Employee calendar accessed via manager route returns employee events only
- _user_category() correctly classifies email addresses
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from app.integrations.graph.mock_adapter import (
    MockGraphCalendarAdapter,
    _user_category,
    _event_visible_to,
)

_NOW = datetime.now(timezone.utc)
_START = _NOW.replace(hour=0, minute=0, second=0, microsecond=0)
_END = _START + timedelta(days=14)

# Canonical demo emails used across tests
ALEX_EMAIL = "a.morgan@contoso.com"
JAMIE_EMAIL = "jamie.lee@dev.local"   # exactly what the mock login returns
ADMIN_EMAIL = "admin.user@contoso.com"


# ---------------------------------------------------------------------------
# _user_category helper
# ---------------------------------------------------------------------------

class TestUserCategory:

    def test_manager_plain(self):
        assert _user_category("a.morgan@contoso.com") == "manager"

    def test_manager_legacy(self):
        assert _user_category("manager@contoso.com") == "manager"

    def test_employee_jamie(self):
        assert _user_category("jamie.lee@dev.local") == "employee"

    def test_employee_j_lee(self):
        assert _user_category("j.lee@contoso.com") == "employee"

    def test_employee_keyword(self):
        assert _user_category("employee@example.com") == "employee"

    def test_admin(self):
        assert _user_category("admin.user@contoso.com") == "admin"

    def test_other_staff_is_manager(self):
        assert _user_category("s.connor@contoso.com") == "manager"
        assert _user_category("d.walsh@contoso.com") == "manager"


# ---------------------------------------------------------------------------
# _event_visible_to helper
# ---------------------------------------------------------------------------

class TestEventVisibleTo:

    def test_shared_event_visible_to_manager(self):
        event = {"shared": True, "organizer": "someone@contoso.com", "attendees": []}
        assert _event_visible_to(event, ALEX_EMAIL) is True

    def test_shared_event_visible_to_employee(self):
        event = {"shared": True, "organizer": "someone@contoso.com", "attendees": []}
        assert _event_visible_to(event, JAMIE_EMAIL) is True

    def test_admin_sees_everything(self):
        event = {"organizer": "j.lee@contoso.com", "attendees": []}
        assert _event_visible_to(event, ADMIN_EMAIL) is True

    def test_manager_event_visible_to_manager(self):
        event = {"organizer": "a.morgan@contoso.com", "attendees": []}
        assert _event_visible_to(event, ALEX_EMAIL) is True

    def test_manager_event_not_visible_to_employee(self):
        event = {"organizer": "a.morgan@contoso.com", "attendees": []}
        assert _event_visible_to(event, JAMIE_EMAIL) is False

    def test_employee_event_visible_to_employee(self):
        event = {"organizer": "j.lee@contoso.com", "attendees": []}
        assert _event_visible_to(event, JAMIE_EMAIL) is True

    def test_employee_event_not_visible_to_manager(self):
        event = {"organizer": "j.lee@contoso.com", "attendees": []}
        assert _event_visible_to(event, ALEX_EMAIL) is False

    def test_exact_email_match_attendee(self):
        # Voice-created event where exact email was stored
        event = {"organizer": "a.morgan@contoso.com", "attendees": [JAMIE_EMAIL]}
        assert _event_visible_to(event, JAMIE_EMAIL) is True

    def test_category_attendee_match(self):
        # Event has attendee "j.lee@contoso.com" but Jamie logs in as "jamie.lee@dev.local"
        # Both are employee category — should still be visible
        event = {"organizer": "a.morgan@contoso.com", "attendees": ["j.lee@contoso.com"]}
        assert _event_visible_to(event, JAMIE_EMAIL) is True


# ---------------------------------------------------------------------------
# MockGraphCalendarAdapter — data separation
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter():
    return MockGraphCalendarAdapter()


@pytest.mark.asyncio
class TestCalendarSeparation:

    async def test_alex_has_events(self, adapter):
        events = await adapter.get_events(ALEX_EMAIL, _START, _END)
        assert len(events) > 0, "Alex should have calendar events"

    async def test_jamie_has_events(self, adapter):
        events = await adapter.get_events(JAMIE_EMAIL, _START, _END)
        assert len(events) > 0, "Jamie should have calendar events"

    async def test_calendars_are_not_identical(self, adapter):
        alex_events = await adapter.get_events(ALEX_EMAIL, _START, _END)
        jamie_events = await adapter.get_events(JAMIE_EMAIL, _START, _END)
        alex_ids = {e["event_id"] for e in alex_events}
        jamie_ids = {e["event_id"] for e in jamie_events}
        # They may share some events but must not be completely identical
        assert alex_ids != jamie_ids, (
            "Alex and Jamie have identical calendars — separation is broken"
        )

    async def test_shared_events_appear_for_both(self, adapter):
        alex_events = await adapter.get_events(ALEX_EMAIL, _START, _END)
        jamie_events = await adapter.get_events(JAMIE_EMAIL, _START, _END)
        alex_ids = {e["event_id"] for e in alex_events}
        jamie_ids = {e["event_id"] for e in jamie_events}
        shared = alex_ids & jamie_ids
        assert len(shared) > 0, "There should be at least one shared event (team standup etc.)"

    async def test_manager_private_events_not_visible_to_employee(self, adapter):
        """Budget review and board prep are Alex-only."""
        jamie_events = await adapter.get_events(JAMIE_EMAIL, _START, _END)
        jamie_subjects = {e["subject"] for e in jamie_events}
        assert "Q3 Budget Review with CFO" not in jamie_subjects
        assert "Board Presentation Prep" not in jamie_subjects

    async def test_employee_private_events_not_visible_to_manager_own_calendar(self, adapter):
        """Jamie's focus blocks should NOT appear in Alex's own calendar."""
        alex_events = await adapter.get_events(ALEX_EMAIL, _START, _END)
        alex_subjects = {e["subject"] for e in alex_events}
        assert "IPA-214 — Graph API Integration (Focus Block)" not in alex_subjects

    async def test_admin_sees_all_events(self, adapter):
        alex_events = await adapter.get_events(ALEX_EMAIL, _START, _END)
        jamie_events = await adapter.get_events(JAMIE_EMAIL, _START, _END)
        admin_events = await adapter.get_events(ADMIN_EMAIL, _START, _END)
        all_ids = {e["event_id"] for e in alex_events} | {e["event_id"] for e in jamie_events}
        admin_ids = {e["event_id"] for e in admin_events}
        assert all_ids.issubset(admin_ids), "Admin should see every event that any user sees"

    async def test_voice_created_event_visible_to_owner(self, adapter):
        """A meeting created by Alex should appear in Alex's calendar."""
        start_dt = _NOW + timedelta(days=1, hours=14)
        end_dt = start_dt + timedelta(hours=1)
        created = await adapter.create_event(
            user_email=ALEX_EMAIL,
            subject="Test Meeting",
            start=start_dt,
            end=end_dt,
            attendees=[],
        )
        events = await adapter.get_events(ALEX_EMAIL, _START, _END)
        ids = {e["event_id"] for e in events}
        assert created["event_id"] in ids

    async def test_voice_created_event_with_invitee_visible_to_invitee(self, adapter):
        """A meeting created by Alex with Jamie as attendee should appear on Jamie's calendar."""
        start_dt = _NOW + timedelta(days=2, hours=10)
        end_dt = start_dt + timedelta(hours=1)
        created = await adapter.create_event(
            user_email=ALEX_EMAIL,
            subject="Shared New Meeting",
            start=start_dt,
            end=end_dt,
            attendees=[JAMIE_EMAIL],
        )
        jamie_events = await adapter.get_events(JAMIE_EMAIL, _START, _END)
        jamie_ids = {e["event_id"] for e in jamie_events}
        assert created["event_id"] in jamie_ids, (
            "Meeting with Jamie as attendee must appear in Jamie's calendar"
        )

    async def test_voice_created_event_not_visible_to_uninvited_employee(self, adapter):
        """Alex's private meeting (no Jamie attendee) must NOT appear in Jamie's calendar."""
        start_dt = _NOW + timedelta(days=2, hours=15)
        end_dt = start_dt + timedelta(hours=1)
        created = await adapter.create_event(
            user_email=ALEX_EMAIL,
            subject="Alex Private Meeting",
            start=start_dt,
            end=end_dt,
            attendees=["cfo@contoso.com"],  # CFO is manager category
        )
        jamie_events = await adapter.get_events(JAMIE_EMAIL, _START, _END)
        jamie_ids = {e["event_id"] for e in jamie_events}
        assert created["event_id"] not in jamie_ids, (
            "Alex's private meeting must NOT appear in Jamie's calendar"
        )

    async def test_deleted_event_removed_for_both(self, adapter):
        """Deleting a shared event removes it from both calendars."""
        # Find the shared standup
        alex_events = await adapter.get_events(ALEX_EMAIL, _START, _END)
        standup = next((e for e in alex_events if "Standup" in e["subject"]), None)
        assert standup is not None, "Team standup must exist"

        await adapter.delete_event(standup["event_id"])

        alex_after = await adapter.get_events(ALEX_EMAIL, _START, _END)
        jamie_after = await adapter.get_events(JAMIE_EMAIL, _START, _END)
        assert standup["event_id"] not in {e["event_id"] for e in alex_after}
        assert standup["event_id"] not in {e["event_id"] for e in jamie_after}
