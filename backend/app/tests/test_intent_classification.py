"""
Tests for the hybrid intent classifier — rules engine.

Covers:
- Intent mapping for all supported command types
- Date entity extraction for every weekday (Monday–Sunday)
- Relative date phrases: tomorrow, next X, this X
- Time entity extraction including bare "at X" format
- Duration extraction
- Person entity extraction and cleanup
- Ambiguous / unknown commands
"""

from __future__ import annotations

import pytest
from datetime import date, timedelta

from app.intents.models import EntityType, Intent
from app.intents.rules_engine import RulesClassifier

_clf = RulesClassifier()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _intent(text: str) -> Intent:
    return _clf.classify(text).intent


def _entity(text: str, entity_type: EntityType) -> str | None:
    result = _clf.classify(text)
    for e in result.entities:
        if e.type == entity_type:
            return e.value
    return None


def _date_entity(text: str) -> str | None:
    return _entity(text, EntityType.DATE)


def _time_entity(text: str) -> str | None:
    return _entity(text, EntityType.TIME)


def _person_entity(text: str) -> str | None:
    return _entity(text, EntityType.PERSON)


def _duration_entity(text: str) -> str | None:
    return _entity(text, EntityType.DURATION)


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

class TestIntentClassification:

    def test_read_emails(self):
        assert _intent("Read my emails") == Intent.READ_EMAILS

    def test_read_emails_check_inbox(self):
        assert _intent("Check my inbox") == Intent.READ_EMAILS

    def test_read_emails_unread(self):
        assert _intent("Show me my unread emails") == Intent.READ_EMAILS

    def test_read_emails_show_me(self):
        assert _intent("Show me my emails") == Intent.READ_EMAILS

    def test_summarise_emails(self):
        assert _intent("Summarise my emails") == Intent.SUMMARISE_EMAILS

    def test_summarise_emails_give_summary(self):
        assert _intent("Give me a summary of my messages") == Intent.SUMMARISE_EMAILS

    def test_send_email(self):
        assert _intent("Send an email to Jamie about the project update") == Intent.SEND_EMAIL

    def test_list_calendar_today(self):
        assert _intent("What's on my calendar today?") == Intent.LIST_CALENDAR_EVENTS

    def test_list_calendar_week(self):
        assert _intent("Show me this week's meetings") == Intent.LIST_CALENDAR_EVENTS

    def test_list_calendar_show_meetings(self):
        assert _intent("Show my meetings") == Intent.LIST_CALENDAR_EVENTS

    def test_list_calendar_what_do_i_have(self):
        assert _intent("What do I have today?") == Intent.LIST_CALENDAR_EVENTS

    def test_list_calendar_friday(self):
        assert _intent("What do I have on Friday?") == Intent.LIST_CALENDAR_EVENTS

    def test_check_availability(self):
        assert _intent("Check availability for Jamie") == Intent.CHECK_AVAILABILITY

    def test_create_meeting_schedule(self):
        assert _intent("Schedule a meeting with Jamie tomorrow at 2 PM") == Intent.CREATE_MEETING

    def test_create_meeting_book(self):
        assert _intent("Book a one-hour check-in with Ali on Monday at 10") == Intent.CREATE_MEETING

    def test_create_meeting_book_hyphen(self):
        assert _intent("Book a one-hour meeting with Jamie tomorrow at 2 PM") == Intent.CREATE_MEETING

    def test_create_meeting_set_up(self):
        assert _intent("Set up a project kickoff with Omar next Monday at 9 AM") == Intent.CREATE_MEETING

    def test_create_meeting_add(self):
        assert _intent("Add a team standup tomorrow at 9 AM") == Intent.CREATE_MEETING

    def test_modify_meeting(self):
        assert _intent("Move my standup to Wednesday at 10") == Intent.MODIFY_MEETING

    def test_modify_meeting_reschedule(self):
        assert _intent("Reschedule the review meeting to Friday at 3 PM") == Intent.MODIFY_MEETING

    def test_delete_meeting(self):
        assert _intent("Cancel my review meeting on Thursday") == Intent.DELETE_MEETING

    def test_delete_meeting_delete(self):
        assert _intent("Delete my 3 PM meeting") == Intent.DELETE_MEETING

    def test_show_employee_calendar(self):
        assert _intent("Show Sarah's calendar") == Intent.SHOW_EMPLOYEE_CALENDAR

    def test_show_employee_calendar_check(self):
        assert _intent("Check Jamie's schedule for this week") == Intent.SHOW_EMPLOYEE_CALENDAR

    def test_show_employee_calendar_what_meetings(self):
        assert _intent("What meetings does Sarah have?") == Intent.SHOW_EMPLOYEE_CALENDAR

    def test_own_calendar_not_employee(self):
        # "What's on my calendar" must NOT trigger SHOW_EMPLOYEE_CALENDAR
        assert _intent("What's on my calendar today?") == Intent.LIST_CALENDAR_EVENTS

    def test_help(self):
        assert _intent("help") == Intent.HELP

    def test_unknown(self):
        assert _intent("xyzzy frobulate the glorp") == Intent.UNKNOWN


# ---------------------------------------------------------------------------
# Weekday date extraction — all 7 days
# ---------------------------------------------------------------------------

class TestWeekdayDateExtraction:
    """Every weekday must extract the correct future date entity."""

    def _expected_date(self, day_offset: int) -> str:
        """Return ISO date string for the next occurrence of a weekday (0=Mon … 6=Sun)."""
        today = date.today()
        days_ahead = (day_offset - today.weekday()) % 7 or 7
        return (today + timedelta(days=days_ahead)).isoformat()

    def test_monday(self):
        result = _date_entity("Schedule a meeting with Jamie on Monday at 2 PM")
        assert result == self._expected_date(0), f"Monday failed: got {result}"

    def test_tuesday(self):
        result = _date_entity("Schedule a meeting with Jamie on Tuesday at 3 PM")
        assert result == self._expected_date(1), f"Tuesday failed: got {result}"

    def test_wednesday(self):
        result = _date_entity("Book a sync with Sarah on Wednesday at 11 AM")
        assert result == self._expected_date(2), f"Wednesday failed: got {result}"

    def test_thursday(self):
        result = _date_entity("Cancel my review meeting on Thursday")
        assert result == self._expected_date(3), f"Thursday failed: got {result}"

    def test_friday(self):
        result = _date_entity("What do I have on Friday?")
        assert result == self._expected_date(4), f"Friday failed: got {result}"

    def test_saturday(self):
        result = _date_entity("Set up a call on Saturday at 10 AM")
        assert result == self._expected_date(5), f"Saturday failed: got {result}"

    def test_sunday(self):
        result = _date_entity("Schedule a meeting on Sunday morning")
        assert result == self._expected_date(6), f"Sunday failed: got {result}"

    def test_next_monday(self):
        result = _date_entity("Schedule a meeting next Monday at 9 AM")
        assert result == self._expected_date(0)

    def test_next_friday(self):
        result = _date_entity("Book a check-in with Ali next Friday at 2 PM")
        assert result == self._expected_date(4)

    def test_this_thursday(self):
        result = _date_entity("Schedule a call this Thursday at 11")
        assert result == self._expected_date(3)

    def test_this_friday(self):
        result = _date_entity("Set up a kickoff this Friday morning")
        assert result == self._expected_date(4)

    def test_tomorrow(self):
        expected = (date.today() + timedelta(days=1)).isoformat()
        result = _date_entity("Schedule a meeting with Jamie tomorrow at 2 PM")
        assert result == expected

    def test_today(self):
        expected = date.today().isoformat()
        result = _date_entity("What do I have today?")
        assert result == expected


# ---------------------------------------------------------------------------
# Time entity extraction
# ---------------------------------------------------------------------------

class TestTimeExtraction:
    # All texts must be complete commands that classify to a known intent
    # so that _extract_entities() runs and produces a TIME entity.

    def test_am_explicit(self):
        assert _time_entity("Schedule a meeting with Jamie tomorrow at 9 AM") == "09:00"

    def test_pm_explicit(self):
        assert _time_entity("Schedule a meeting with Jamie tomorrow at 2 PM") == "14:00"

    def test_pm_explicit_3(self):
        assert _time_entity("Book a call with Ali tomorrow at 3 PM") == "15:00"

    def test_24h_format(self):
        assert _time_entity("Schedule a meeting with Jamie tomorrow at 14:30") == "14:30"

    def test_colon_format_am(self):
        assert _time_entity("Schedule a meeting with Jamie tomorrow at 9:30 AM") == "09:30"

    def test_noon(self):
        assert _time_entity("Schedule a meeting with Jamie at noon tomorrow") == "12:00"

    def test_midnight(self):
        assert _time_entity("Schedule a meeting with Jamie at midnight tomorrow") == "00:00"

    def test_oclock(self):
        assert _time_entity("Schedule a meeting with Jamie tomorrow at 3 o'clock") == "15:00"

    def test_half_past(self):
        assert _time_entity("Schedule a meeting with Jamie tomorrow at half past 2") == "14:30"

    # Core fix: bare "at X" without AM/PM or colon
    def test_at_11_bare(self):
        assert _time_entity("Schedule a meeting with Jamie on Thursday at 11") == "11:00"

    def test_at_3_bare(self):
        # 3 is ambiguous (1-6) → assumes PM
        assert _time_entity("Book a check-in with Ali on Monday at 3") == "15:00"

    def test_at_9_bare(self):
        # 9 is > 6 → no PM assumption → 09:00
        assert _time_entity("Schedule a standup with Sarah on Tuesday at 9") == "09:00"

    def test_at_10_bare(self):
        assert _time_entity("Book a call with Jamie on Friday at 10") == "10:00"

    def test_morning_period(self):
        assert _time_entity("Schedule a meeting with Jamie on Thursday morning") == "09:00"

    def test_afternoon_period(self):
        assert _time_entity("Book a call with Ali on Friday afternoon") == "14:00"


# ---------------------------------------------------------------------------
# Duration entity extraction
# ---------------------------------------------------------------------------

class TestDurationExtraction:
    # _DURATION_PATTERN matches "for X minutes/hours" and word forms like "one hour"
    # Adjective forms like "30-minute meeting" are embedded in booking patterns
    # but don't produce a standalone DURATION entity (defaults to 60 min).

    def test_for_minutes(self):
        assert _duration_entity("Schedule a meeting for 45 minutes with Jamie tomorrow") == "45"

    def test_for_hours(self):
        assert _duration_entity("Book a call for 2 hours with Ali on Friday") == "120"

    def test_word_one_hour(self):
        assert _duration_entity("Book a one hour check-in with Ali on Monday at 10 AM") == "60"

    def test_word_one_hour_hyphen(self):
        assert _duration_entity("Book a one-hour check-in with Ali on Monday at 10 AM") == "60"

    def test_word_half_hour(self):
        assert _duration_entity("Book a half an hour meeting with Sarah tomorrow") == "30"


# ---------------------------------------------------------------------------
# Person entity extraction
# ---------------------------------------------------------------------------

class TestPersonExtraction:

    def test_with_single_name(self):
        assert _person_entity("Schedule a meeting with Jamie tomorrow at 2 PM") == "Jamie"

    def test_with_full_name(self):
        result = _person_entity("Book a call with Sarah Connor on Friday at 3 PM")
        assert result is not None
        assert "Sarah" in result

    def test_person_not_polluted_by_day(self):
        # Person must NOT include the day keyword
        person = _person_entity("Schedule a meeting with Jamie on Tuesday at 3 PM")
        assert person == "Jamie", f"Person was '{person}', expected 'Jamie'"

    def test_person_not_polluted_by_time(self):
        person = _person_entity("Schedule a meeting with Ali at 2 PM tomorrow")
        assert person == "Ali", f"Person was '{person}', expected 'Ali'"

    def test_employee_calendar_person(self):
        person = _person_entity("Show Sarah's calendar")
        assert person is not None
        assert "Sarah" in person

    def test_send_email_recipient(self):
        person = _person_entity("Send an email to James about the project")
        assert person is not None
        assert "James" in person


# ---------------------------------------------------------------------------
# Confidence scores
# ---------------------------------------------------------------------------

class TestConfidence:

    def test_high_confidence_explicit(self):
        result = _clf.classify("Read my emails")
        assert result.confidence >= 0.90

    def test_high_confidence_meeting(self):
        result = _clf.classify("Schedule a meeting with Jamie tomorrow at 2 PM")
        assert result.confidence >= 0.90

    def test_unknown_zero_confidence(self):
        result = _clf.classify("xyzzy frobulate the glorp")
        assert result.confidence == 0.0
        assert result.clarification_needed is True
