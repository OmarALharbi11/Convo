"""Intent classifier tests — covers all intents, entity extraction, and edge cases."""

from __future__ import annotations

import pytest

from app.intents.models import EntityType, Intent
from app.intents.rules_engine import RulesClassifier


@pytest.fixture
def clf():
    return RulesClassifier()


class TestReadEmails:
    def test_read_my_emails(self, clf):
        r = clf.classify("Read my emails")
        assert r.intent == Intent.READ_EMAILS
        assert r.confidence >= 0.7

    def test_check_inbox(self, clf):
        r = clf.classify("Check my inbox")
        assert r.intent == Intent.READ_EMAILS

    def test_whats_in_inbox(self, clf):
        r = clf.classify("What's in my inbox?")
        assert r.intent == Intent.READ_EMAILS

    def test_show_messages(self, clf):
        r = clf.classify("Show me my messages")
        assert r.intent == Intent.READ_EMAILS

    def test_any_new_emails(self, clf):
        r = clf.classify("Do I have any new emails?")
        assert r.intent == Intent.READ_EMAILS


class TestSummariseEmails:
    def test_summarise_emails(self, clf):
        r = clf.classify("Summarise my emails")
        assert r.intent == Intent.SUMMARISE_EMAILS

    def test_summarize_unread(self, clf):
        r = clf.classify("Summarize my unread emails from this morning")
        assert r.intent == Intent.SUMMARISE_EMAILS

    def test_give_summary(self, clf):
        r = clf.classify("Give me a summary of my messages")
        assert r.intent == Intent.SUMMARISE_EMAILS


class TestSendEmail:
    def test_send_email_to_person(self, clf):
        r = clf.classify("Send an email to Sarah about the project update")
        assert r.intent == Intent.SEND_EMAIL
        assert r.requires_confirmation is True

    def test_send_email_extracts_person(self, clf):
        r = clf.classify("Send an email to David about the Q3 review")
        assert r.intent == Intent.SEND_EMAIL
        persons = [e for e in r.entities if e.type == EntityType.PERSON]
        assert len(persons) > 0
        assert "David" in persons[0].value

    def test_send_email_extracts_subject(self, clf):
        r = clf.classify("Send an email to John about the budget report")
        subjects = [e for e in r.entities if e.type == EntityType.EMAIL_SUBJECT]
        assert len(subjects) > 0

    def test_email_requires_confirmation(self, clf):
        r = clf.classify("Email Sarah about tomorrow's meeting")
        assert r.requires_confirmation is True


class TestCalendar:
    def test_what_does_my_day_look_like(self, clf):
        r = clf.classify("What does my day look like?")
        assert r.intent == Intent.LIST_CALENDAR_EVENTS

    def test_what_do_i_have_today(self, clf):
        r = clf.classify("What do I have today?")
        assert r.intent == Intent.LIST_CALENDAR_EVENTS

    def test_show_my_schedule(self, clf):
        r = clf.classify("Show me my schedule for this week")
        assert r.intent == Intent.LIST_CALENDAR_EVENTS

    def test_list_meetings(self, clf):
        r = clf.classify("List my meetings")
        assert r.intent == Intent.LIST_CALENDAR_EVENTS

    def test_afternoon_schedule(self, clf):
        r = clf.classify("What does my afternoon look like?")
        assert r.intent == Intent.LIST_CALENDAR_EVENTS


class TestCheckAvailability:
    def test_is_sarah_available(self, clf):
        r = clf.classify("Is Sarah available tomorrow?")
        assert r.intent == Intent.CHECK_AVAILABILITY

    def test_check_availability_explicit(self, clf):
        r = clf.classify("Check availability for the finance team")
        assert r.intent == Intent.CHECK_AVAILABILITY

    def test_when_is_john_free(self, clf):
        r = clf.classify("When is John free this week?")
        assert r.intent == Intent.CHECK_AVAILABILITY


class TestCreateMeeting:
    def test_schedule_meeting(self, clf):
        r = clf.classify("Schedule a meeting with Sarah tomorrow at 2 PM")
        assert r.intent == Intent.CREATE_MEETING

    def test_book_meeting(self, clf):
        r = clf.classify("Book a call with the team on Friday")
        assert r.intent == Intent.CREATE_MEETING

    def test_schedule_extracts_person(self, clf):
        r = clf.classify("Schedule a meeting with John tomorrow at 3 PM")
        persons = [e for e in r.entities if e.type == EntityType.PERSON]
        assert len(persons) > 0

    def test_schedule_extracts_time(self, clf):
        r = clf.classify("Schedule a meeting at 2 PM")
        times = [e for e in r.entities if e.type == EntityType.TIME]
        assert len(times) > 0
        assert "14:00" in times[0].value

    def test_schedule_extracts_date(self, clf):
        r = clf.classify("Schedule a meeting tomorrow at 10 AM")
        dates = [e for e in r.entities if e.type == EntityType.DATE]
        assert len(dates) > 0


class TestModifyMeeting:
    def test_reschedule_meeting(self, clf):
        r = clf.classify("Reschedule my 3 PM meeting to Friday")
        assert r.intent == Intent.MODIFY_MEETING
        assert r.requires_confirmation is True

    def test_move_meeting(self, clf):
        r = clf.classify("Move my afternoon meeting to next Monday")
        assert r.intent == Intent.MODIFY_MEETING

    def test_modify_requires_confirmation(self, clf):
        r = clf.classify("Change my 2 PM meeting to Thursday")
        assert r.requires_confirmation is True


class TestDeleteMeeting:
    def test_cancel_meeting(self, clf):
        r = clf.classify("Cancel my standup tomorrow")
        assert r.intent == Intent.DELETE_MEETING
        assert r.requires_confirmation is True

    def test_delete_event(self, clf):
        r = clf.classify("Delete the budget review meeting")
        assert r.intent == Intent.DELETE_MEETING


class TestHelpAndRepeat:
    def test_help(self, clf):
        r = clf.classify("help")
        assert r.intent == Intent.HELP

    def test_what_can_you_do(self, clf):
        r = clf.classify("What can you do?")
        assert r.intent == Intent.HELP

    def test_repeat_that(self, clf):
        r = clf.classify("Repeat that")
        assert r.intent == Intent.REPEAT_LAST

    def test_say_again(self, clf):
        r = clf.classify("Say that again")
        assert r.intent == Intent.REPEAT_LAST


class TestUnknown:
    def test_gibberish_is_unknown(self, clf):
        r = clf.classify("xyzzy plugh frobozz")
        assert r.intent == Intent.UNKNOWN
        assert r.clarification_needed is True
        assert r.clarification_question is not None

    def test_empty_is_unknown(self, clf):
        r = clf.classify("   ")
        assert r.intent == Intent.UNKNOWN
