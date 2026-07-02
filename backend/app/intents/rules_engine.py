"""
Rule-based intent classifier using regex pattern matching.

Design principles:
- Deterministic and fast — no external API calls required.
- Explainable — each classification includes the matched pattern name.
- Comprehensive — multiple phrasings per intent to handle natural variation.
- Confidence scoring — longer/more specific matches score higher.
- Entity extraction — persons, dates, times, durations, subjects, titles extracted
  from the matched text using named capture groups and secondary scans.

This forms the first tier of the HybridIntentClassifier.  When confidence
is low (< 0.6) and LLM parsing is enabled, the LLM parser is consulted.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

from app.intents.models import (
    ClassifiedIntent,
    EntityType,
    ExtractedEntity,
    Intent,
)

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------
# Each entry: (pattern_name, regex, intent, base_confidence)
# Patterns are tried in order; first match wins.

_PATTERNS: list[tuple[str, str, Intent, float]] = [
    # --- Read emails ---
    ("read_emails_explicit", r"\bread\s+(my\s+)?(latest|recent|new|unread|inbox|all)?\s*e?mails?\b", Intent.READ_EMAILS, 0.95),
    ("check_inbox", r"\b(check|open|show|get)\s+(me\s+)?(my\s+)?(inbox|e?mails?|messages?)\b", Intent.READ_EMAILS, 0.90),
    ("show_unread", r"\bshow\s+me\s+(my\s+)?(unread|new|latest|recent)?\s*e?mails?\b", Intent.READ_EMAILS, 0.90),
    ("whats_in_inbox", r"\bwhat(?:'s|\s+is|\s+are)\s+(in\s+)?(my\s+)?(inbox|e?mails?|messages?)\b", Intent.READ_EMAILS, 0.88),
    ("any_new_emails", r"\b(any|do\s+i\s+have)\s+(new|unread)?\s*(e?mails?|messages?)\b", Intent.READ_EMAILS, 0.85),

    # --- Summarise emails ---
    ("summarise_emails_explicit", r"\b(summarise?|summarize|summary\s+of)\s+(my\s+)?(e?mails?|messages?|inbox|unread)\b", Intent.SUMMARISE_EMAILS, 0.95),
    ("give_summary", r"\bgive\s+(me\s+)?(a\s+)?summary\s+of\s+(my\s+)?(e?mails?|messages?)\b", Intent.SUMMARISE_EMAILS, 0.90),
    ("key_points_email", r"\bwhat\s+are\s+the\s+key\s+(points|highlights)\s+(of\s+)?(my\s+)?(e?mails?|messages?)\b", Intent.SUMMARISE_EMAILS, 0.85),

    # --- Send email ---
    ("send_email_explicit", r"\b(send|write|compose|draft)\s+(an?\s+)?e?mail\s+(to\s+)?(?P<recipient>[\w\s]+?)(?:\s+about\s+(?P<subject>.+?))?(?:\s+regarding\s+(?P<subject2>.+?))?$", Intent.SEND_EMAIL, 0.95),
    ("email_someone", r"\be?mail\s+(?P<recipient>[\w\s]+?)(?:\s+about\s+(?P<subject>.+?))?$", Intent.SEND_EMAIL, 0.85),
    ("reply_to", r"\b(reply|respond)\s+(to\s+)?(?P<recipient>[\w\s]+?)(?:\s+about\s+(?P<subject>.+?))?$", Intent.SEND_EMAIL, 0.80),

    # --- Show employee calendar (MUST come before list_calendar to avoid false matches) ---
    # Require possessive 's — "Sarah's calendar" not "my calendar"
    ("show_employee_calendar", r"\b(show|view|open|check|see)\s+(?P<person>(?!my\b|our\b|the\b|your\b|their\b)[A-Za-z]+(?:\s+[A-Za-z]+)?)'s?\s+(calendar|schedule|agenda|meetings?|events?|day|week)\b", Intent.SHOW_EMPLOYEE_CALENDAR, 0.93),
    ("whats_employee_calendar", r"\bwhat(?:'s|\s+is|\s+does)\s+(?P<person>(?!my\b|our\b|the\b|your\b|their\b)[A-Za-z]+(?:\s+[A-Za-z]+)?)'s?\s+(calendar|schedule|day|week|meetings?)\s*(look\s+like)?\b", Intent.SHOW_EMPLOYEE_CALENDAR, 0.90),
    ("employee_meetings_query", r"\bwhat\s+meetings?\s+does\s+(?P<person>(?!my\b|our\b|the\b|your\b|their\b)[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+have\b", Intent.SHOW_EMPLOYEE_CALENDAR, 0.88),

    # --- List calendar / schedule ---
    ("whats_on_my_calendar", r"\bwhat(?:'s|\s+is|\s+are)\s+on\s+(my\s+)?(calendar|schedule|agenda)\b", Intent.LIST_CALENDAR_EVENTS, 0.95),
    ("whats_my_schedule", r"\bwhat(?:'s|\s+does|\s+is)\s+(my\s+)?(schedule|calendar|agenda|day|week|morning|afternoon|evening)\s*(look\s+like|today|tomorrow|this\s+week)?\b", Intent.LIST_CALENDAR_EVENTS, 0.95),
    ("list_meetings", r"\b(list|show|view|see|get|check)\s+(me\s+)?(my\s+)?(meetings?|events?|appointments?|calendar|schedule)\b", Intent.LIST_CALENDAR_EVENTS, 0.90),
    ("show_this_weeks_meetings", r"\bshow\s+me\s+(this\s+week'?s?\s+)?(meetings?|schedule|calendar|events?)\b", Intent.LIST_CALENDAR_EVENTS, 0.90),
    ("show_my_schedule", r"\bshow\s+me\s+(my\s+)?(schedule|calendar)\s*(for\s+.*)?\b", Intent.LIST_CALENDAR_EVENTS, 0.90),
    ("what_do_i_have", r"\bwhat\s+do\s+i\s+have\s+(today|tomorrow|this\s+(morning|afternoon|week)|on\s+\w+day)\b", Intent.LIST_CALENDAR_EVENTS, 0.90),
    ("am_i_free", r"\bam\s+i\s+(free|available|busy)\s+(today|tomorrow|on\s+\w+day|this\s+(morning|afternoon))?\b", Intent.LIST_CALENDAR_EVENTS, 0.85),
    ("todays_meetings", r"\b(today'?s?|tomorrow'?s?)\s+(meetings?|schedule|calendar|agenda)\b", Intent.LIST_CALENDAR_EVENTS, 0.88),

    # --- Check availability ---
    ("check_availability_explicit", r"\bcheck\s+(availability|free\s+slots?|free\s+time|schedule)\s+(for\s+)?(?P<person>[\w\s@.]+)\b", Intent.CHECK_AVAILABILITY, 0.90),
    ("is_person_available", r"\bis\s+(?P<person>(?!my\b|our\b|the\b|your\b|their\b)[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(free|available|around|busy)\b", Intent.CHECK_AVAILABILITY, 0.88),
    ("when_is_free", r"\bwhen\s+is\s+(?P<person>[\w\s]+?)\s+(free|available)\b", Intent.CHECK_AVAILABILITY, 0.88),

    # --- Create meeting ---
    # "book a 30-minute/one-hour [meeting type] with [person]"
    ("book_duration_meeting", r"\b(book|schedule|add|set\s+up)\s+(an?\s+)?(?:\d+[-\s]?(?:minute|min|hour|hr)s?|(?:one|two|three|four)[-\s]+(?:hour|minute|min|hr)s?|half[-\s]an?\s+hour)[-\s]*(check.?in|meeting|call|sync|session|standup|stand.?up|catch.?up|one.?on.?one|1.?on.?1)\s+(with\s+(?P<person>[\w\s]+?))?\s*(tomorrow|today|on\s+\w+day|next\s+\w+)?\b", Intent.CREATE_MEETING, 0.95),
    ("schedule_meeting_simple", r"\b(schedule|book|set\s+up|arrange|organise?|organize)\s+(a\s+)?(meeting|call|sync|session|catch.?up|standup|stand.?up|check.?in|kick.?off|kickoff|review|briefing|one.?on.?one|1.?on.?1)\s+(with\s+(?P<person>[\w\s]+?))?\s*(tomorrow|today|on\s+\w+day)?(\s+at\s+(?P<time>[\d:apmAPM\s]+))?\b", Intent.CREATE_MEETING, 0.92),
    ("schedule_titled_meeting", r"\b(schedule|book|set\s+up|arrange|organise?|organize|create)\s+(a\s+)?(?P<title>[\w][\w\s]+?)\s+(with\s+(?P<person>[\w\s]+?))?\s*(tomorrow|today|on\s+\w+day|next\s+\w+)?(\s+at\s+(?P<time>[\d:apmAPM\s]+))?\s*$", Intent.CREATE_MEETING, 0.78),
    ("book_time_with", r"\bbook\s+(some\s+)?(time|a\s+slot)\s+with\s+(?P<person>[\w\s]+)\b", Intent.CREATE_MEETING, 0.88),
    ("create_meeting_explicit", r"\bcreate\s+(a\s+)?(new\s+)?(meeting|event|appointment)\b", Intent.CREATE_MEETING, 0.85),
    # "add a [optional adjective/noun] [meeting type]"
    ("add_meeting", r"\badd\s+(a\s+)?(?:[\w]+\s+)?(meeting|event|appointment|check.?in|sync|standup|stand.?up|one.?on.?one|1.?on.?1)\b", Intent.CREATE_MEETING, 0.83),
    ("invite_to_meeting", r"\binvite\s+(?P<person>[\w\s]+?)\s+(to\s+)?(a\s+)?(meeting|call)\b", Intent.CREATE_MEETING, 0.82),

    # --- Modify meeting ---
    ("reschedule_meeting", r"\b(reschedule|move|change|shift|push)\s+(my\s+|the\s+)?(?P<event_ref>[\w\s]*(meeting|call|appointment|event|standup|review|sync|check.?in)[\w\s]*?)\s*(to\s+(?P<date>[\w\s]+?))?(\s+at\s+(?P<time>[\d:apmAPM\s]+))?\b", Intent.MODIFY_MEETING, 0.92),
    ("move_meeting_to", r"\bmove\s+(the\s+|my\s+)?(?P<event_ref>[\w\s]+?)\s+(meeting|call)\s+(to\s+(?P<date>[\w\s]+?))?(\s+at\s+(?P<time>[\d:apmAPM\s]+))?\b", Intent.MODIFY_MEETING, 0.90),
    ("update_meeting", r"\b(update|change|modify)\s+(the\s+|my\s+)?(meeting|event|appointment)\b", Intent.MODIFY_MEETING, 0.82),

    # --- Delete meeting ---
    ("cancel_meeting_explicit", r"\b(cancel|delete|remove)\s+(my\s+|the\s+)?(?P<event_ref>[\w\s]+?)\s*(meeting|appointment|event|call|standup|review|sync)\b", Intent.DELETE_MEETING, 0.92),
    ("cancel_todays", r"\b(cancel|delete)\s+(today'?s?|tomorrow'?s?)\s+(?P<event_ref>[\w\s]*)(meeting|standup|call|event|appointment)?\b", Intent.DELETE_MEETING, 0.88),

    # --- Notifications ---
    ("read_notifications", r"\b(read|check|show|any)\s+(my\s+)?(notifications?|alerts?|reminders?|updates?)\b", Intent.READ_NOTIFICATIONS, 0.88),

    # --- Help ---
    ("help_explicit", r"^\s*(help|what\s+can\s+you\s+do\??|commands?|how\s+do\s+i|what\s+do\s+you\s+(do|support)\??)\s*$", Intent.HELP, 0.98),

    # --- Repeat ---
    ("repeat_last", r"\b(repeat\s+(that|last|what\s+you\s+said)|say\s+that\s+again|what\s+did\s+you\s+say)\b", Intent.REPEAT_LAST, 0.98),
]

# Compile all patterns once at import time
_COMPILED_PATTERNS: list[tuple[str, re.Pattern, Intent, float]] = [
    (name, re.compile(pattern, re.IGNORECASE | re.UNICODE), intent, conf)
    for name, pattern, intent, conf in _PATTERNS
]

# ---------------------------------------------------------------------------
# Time / date extraction helpers
# ---------------------------------------------------------------------------

# Keyword times — matched before regex time patterns
_KEYWORD_TIME_MAP: dict[str, str] = {
    "noon": "12:00",
    "midday": "12:00",
    "midnight": "00:00",
}

# Period-of-day → default start times
_PERIOD_TIME_MAP: dict[str, str] = {
    "morning": "09:00",
    "afternoon": "14:00",
    "evening": "18:00",
    "tonight": "19:00",
    "lunch": "12:00",
    "lunchtime": "12:00",
}

# Relative date keywords — multi-word phrases must appear BEFORE single words
# so the keyword scan (which breaks on first match) finds the most specific form first.
_DATE_KEYWORDS: dict[str, str] = {
    # Multi-word phrases first
    "next monday": "next_monday",
    "next tuesday": "next_tuesday",
    "next wednesday": "next_wednesday",
    "next thursday": "next_thursday",
    "next friday": "next_friday",
    "next saturday": "next_saturday",
    "next sunday": "next_sunday",
    "this monday": "next_monday",
    "this tuesday": "next_tuesday",
    "this wednesday": "next_wednesday",
    "this thursday": "next_thursday",
    "this friday": "next_friday",
    "this saturday": "next_saturday",
    "this sunday": "next_sunday",
    "next week": "next_week",
    "this morning": "today",
    "this afternoon": "today",
    "this evening": "today",
    # Single words
    "today": "today",
    "tomorrow": "tomorrow",
    "monday": "next_monday",
    "tuesday": "next_tuesday",
    "wednesday": "next_wednesday",
    "thursday": "next_thursday",
    "friday": "next_friday",
    "saturday": "next_saturday",
    "sunday": "next_sunday",
    "morning": "today",
    "afternoon": "today",
    "evening": "today",
    "tonight": "today",
}

# Extended time pattern: standard formats + keyword times + o'clock + bare "at X"
_TIME_PATTERN = re.compile(
    r"\b(noon|midday|midnight)\b"
    r"|half\s+past\s+(\d{1,2})\b"
    r"|\b(\d{1,2})(?::(\d{2}))?\s*o'?\s*clock\b"
    r"|\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b"
    r"|(\d{1,2}):(\d{2})\b"
    r"|\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b",  # "at 11", "at 3", "at 9:30"
    re.IGNORECASE,
)

_DURATION_PATTERN = re.compile(
    r"\bfor\s+(\d+)\s+(minute|hour|min|hr)s?\b"
    r"|\b(one|two|three|four|half\s+an?)[-\s]+(hour|minute|min)s?\b",
    re.IGNORECASE,
)
_PERSON_PREFIXES = re.compile(
    r"\b(with|to|from|for|invite)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)
_ABOUT_PATTERN = re.compile(r"\babout\s+(.+?)(?:\s*$|\s+(?:on|at|for|to)\b)", re.IGNORECASE)

# Meeting title from "called X", "titled X", "named X", "for X meeting"
_TITLE_PATTERN = re.compile(
    r"\b(?:called|titled|named)\s+[\"']?([^\"']+?)[\"']?\s*(?:$|with\b|at\b|on\b|for\b|\d)",
    re.IGNORECASE,
)

# "next Monday / this Friday" etc — explicit modifier before a weekday name
_NEXT_DAY_PATTERN = re.compile(
    r"\b(next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.IGNORECASE,
)


class RulesClassifier:
    """Deterministic rule-based intent classifier."""

    def classify(self, text: str) -> ClassifiedIntent:
        text_clean = text.strip()

        # Try each compiled pattern
        for pattern_name, regex, intent, base_confidence in _COMPILED_PATTERNS:
            match = regex.search(text_clean)
            if match:
                entities = self._extract_entities(text_clean, intent, match)
                # Boost confidence if multiple entities extracted
                confidence = min(1.0, base_confidence + 0.02 * len(entities))
                return ClassifiedIntent(
                    intent=intent,
                    entities=entities,
                    confidence=confidence,
                    raw_input=text_clean,
                    matched_pattern=pattern_name,
                )

        # No pattern matched
        return ClassifiedIntent(
            intent=Intent.UNKNOWN,
            entities=[],
            confidence=0.0,
            clarification_needed=True,
            clarification_question=(
                "I didn't quite catch that. Could you rephrase? For example: "
                "'Read my emails', 'Schedule a meeting with Sarah', or 'What's on my calendar today?'"
            ),
            raw_input=text_clean,
            matched_pattern=None,
        )

    def _extract_entities(
        self,
        text: str,
        intent: Intent,
        match: re.Match,
    ) -> list[ExtractedEntity]:
        entities: list[ExtractedEntity] = []

        # Named groups from the pattern
        groups = match.groupdict()

        # Person
        person_raw = groups.get("person") or groups.get("recipient")
        if person_raw and person_raw.strip():
            # Clean common trailing words that leak into the person capture
            person_clean = re.sub(
                r"\s+(meeting|call|event|appointment|calendar|tomorrow|today|at|on|for|next|about)\b.*$",
                "", person_raw.strip(), flags=re.IGNORECASE,
            ).strip()
            if person_clean:
                entities.append(ExtractedEntity(
                    type=EntityType.PERSON,
                    value=person_clean.title(),
                    raw_text=person_raw.strip(),
                    confidence=0.9,
                ))
        else:
            # Fallback: scan for "with/to/from [Name]"
            person_match = _PERSON_PREFIXES.search(text)
            if person_match:
                entities.append(ExtractedEntity(
                    type=EntityType.PERSON,
                    value=person_match.group(2),
                    raw_text=person_match.group(2),
                    confidence=0.75,
                ))

        # Meeting title — "called X", "titled X", "named X"
        if intent in (Intent.CREATE_MEETING, Intent.MODIFY_MEETING):
            title_match = _TITLE_PATTERN.search(text)
            if title_match:
                title_val = title_match.group(1).strip()
                if title_val:
                    entities.append(ExtractedEntity(
                        type=EntityType.MEETING_TITLE,
                        value=title_val.title(),
                        raw_text=title_val,
                        confidence=0.90,
                    ))
            # Also grab the title from pattern's "title" named group if present
            title_group = groups.get("title")
            if title_group and title_group.strip() and not any(e.type == EntityType.MEETING_TITLE for e in entities):
                # Only use if it looks like a meaningful title (more than one word or specific keywords)
                title_clean = title_group.strip()
                if len(title_clean) > 3:
                    entities.append(ExtractedEntity(
                        type=EntityType.MEETING_TITLE,
                        value=title_clean.title(),
                        raw_text=title_clean,
                        confidence=0.75,
                    ))

        # Date — handle "next/this Monday" before generic keyword scan
        next_day_match = _NEXT_DAY_PATTERN.search(text)
        if next_day_match:
            day_name = next_day_match.group(2).lower()
            resolved = self._resolve_relative_date(f"next_{day_name}")
            entities.append(ExtractedEntity(
                type=EntityType.DATE,
                value=resolved,
                raw_text=next_day_match.group(0),
                confidence=0.95,
            ))
        else:
            for keyword, normalized in _DATE_KEYWORDS.items():
                if re.search(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE):
                    entities.append(ExtractedEntity(
                        type=EntityType.DATE,
                        value=self._resolve_relative_date(normalized),
                        raw_text=keyword,
                        confidence=0.95,
                    ))
                    break

        # Time — keyword times first, then regex
        time_entity = self._extract_time(text)
        if time_entity:
            entities.append(time_entity)
        elif not time_entity:
            # Infer time from period-of-day if no explicit time found
            for period, default_time in _PERIOD_TIME_MAP.items():
                if re.search(r"\b" + re.escape(period) + r"\b", text, re.IGNORECASE):
                    entities.append(ExtractedEntity(
                        type=EntityType.TIME,
                        value=default_time,
                        raw_text=period,
                        confidence=0.70,
                    ))
                    break

        # Duration
        dur_entity = self._extract_duration(text)
        if dur_entity:
            entities.append(dur_entity)

        # Subject / topic (for email intents)
        if intent in (Intent.SEND_EMAIL, Intent.SUMMARISE_EMAILS):
            subject_raw = groups.get("subject") or groups.get("subject2")
            if not subject_raw:
                about_match = _ABOUT_PATTERN.search(text)
                if about_match:
                    subject_raw = about_match.group(1).strip()
            if subject_raw and subject_raw.strip():
                entities.append(ExtractedEntity(
                    type=EntityType.EMAIL_SUBJECT,
                    value=subject_raw.strip(),
                    raw_text=subject_raw.strip(),
                    confidence=0.85,
                ))

        # Event reference (for modify/delete)
        if intent in (Intent.MODIFY_MEETING, Intent.DELETE_MEETING):
            event_ref = groups.get("event_ref")
            if event_ref and event_ref.strip():
                # Clean trailing conjunctions
                ref_clean = re.sub(r"\s+(to|with|at|on)\s*$", "", event_ref.strip(), flags=re.IGNORECASE).strip()
                if ref_clean:
                    entities.append(ExtractedEntity(
                        type=EntityType.EVENT_REFERENCE,
                        value=ref_clean,
                        raw_text=ref_clean,
                        confidence=0.80,
                    ))

        return entities

    @staticmethod
    def _extract_time(text: str) -> ExtractedEntity | None:
        """Extract a time entity from text, handling keywords and natural phrases."""
        text_lower = text.lower()

        # Keyword times: noon, midnight, midday
        for keyword, value in _KEYWORD_TIME_MAP.items():
            if re.search(r"\b" + keyword + r"\b", text_lower):
                return ExtractedEntity(
                    type=EntityType.TIME,
                    value=value,
                    raw_text=keyword,
                    confidence=0.98,
                )

        # Regex time pattern
        time_match = _TIME_PATTERN.search(text)
        if not time_match:
            return None

        raw = time_match.group(0)
        normalized = RulesClassifier._normalize_time(raw)
        if normalized:
            return ExtractedEntity(
                type=EntityType.TIME,
                value=normalized,
                raw_text=raw,
                confidence=0.95,
            )
        return None

    @staticmethod
    def _extract_duration(text: str) -> ExtractedEntity | None:
        """Extract a duration entity, including word-form durations."""
        dur_match = _DURATION_PATTERN.search(text)
        if not dur_match:
            return None

        raw = dur_match.group(0)
        # Numeric form: "for 30 minutes", "for 2 hours"
        if dur_match.group(1) and dur_match.group(2):
            amount = int(dur_match.group(1))
            unit = dur_match.group(2).lower()
            minutes = amount * 60 if unit in ("hour", "hr") else amount
            return ExtractedEntity(
                type=EntityType.DURATION,
                value=str(minutes),
                raw_text=raw,
                confidence=0.95,
            )
        # Word form: "one hour", "half an hour"
        if dur_match.group(3) and dur_match.group(4):
            word = dur_match.group(3).lower()
            unit = dur_match.group(4).lower()
            word_map = {"one": 1, "two": 2, "three": 3, "four": 4, "half an": 0, "half a": 0}
            amount = word_map.get(word, 1)
            if "half" in word:
                minutes = 30 if "hour" in unit else 1
            else:
                minutes = amount * 60 if "hour" in unit else amount
            return ExtractedEntity(
                type=EntityType.DURATION,
                value=str(minutes),
                raw_text=raw,
                confidence=0.88,
            )
        return None

    @staticmethod
    def _normalize_time(raw: str) -> str | None:
        """Convert various time formats to HH:MM.

        Handles:
          '2 PM' → '14:00'
          '9:30 AM' → '09:30'
          '3 o'clock' → '15:00' (assumes PM for ambiguous afternoon hours)
          'half past 2' → '14:30'
          '14:30' → '14:30'
          'at 11' → '11:00'
          'at 3' → '15:00' (PM assumption for 1-6)
          'at 9:30' → '09:30'
        """
        raw = raw.strip()
        # Strip "at " prefix — produced by the "at X" time pattern alternation
        raw = re.sub(r"^at\s+", "", raw, flags=re.IGNORECASE).strip()

        # Half past X
        half_past = re.match(r"half\s+past\s+(\d{1,2})", raw, re.IGNORECASE)
        if half_past:
            hour = int(half_past.group(1))
            # Assume PM for hours 1-6 without explicit meridiem
            if 1 <= hour <= 6:
                hour += 12
            return f"{hour:02d}:30"

        # X o'clock
        oclock = re.match(r"(\d{1,2})\s*o'?\s*clock", raw, re.IGNORECASE)
        if oclock:
            hour = int(oclock.group(1))
            # Assume PM for 1-6 (typical meeting hours), AM for 7-11
            if 1 <= hour <= 6:
                hour += 12
            return f"{hour:02d}:00"

        # Standard: 2 PM / 9:30 AM / 14:30
        m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", raw, re.IGNORECASE)
        if not m:
            return None
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        meridiem = (m.group(3) or "").upper()
        if meridiem == "PM" and hour != 12:
            hour += 12
        elif meridiem == "AM" and hour == 12:
            hour = 0
        elif not meridiem and 1 <= hour <= 6:
            # Ambiguous hour without AM/PM — assume PM for typical business hours
            hour += 12
        return f"{hour:02d}:{minute:02d}"

    @staticmethod
    def _resolve_relative_date(normalized: str) -> str:
        """Resolve relative date keywords to ISO date strings."""
        today = date.today()
        if normalized == "today":
            return today.isoformat()
        if normalized == "tomorrow":
            return (today + timedelta(days=1)).isoformat()
        if normalized == "next_week":
            days_until_monday = (7 - today.weekday()) % 7 or 7
            return (today + timedelta(days=days_until_monday)).isoformat()
        for day_name, day_offset in [
            ("monday", 0), ("tuesday", 1), ("wednesday", 2), ("thursday", 3),
            ("friday", 4), ("saturday", 5), ("sunday", 6),
        ]:
            if day_name in normalized:
                days_ahead = (day_offset - today.weekday()) % 7 or 7
                return (today + timedelta(days=days_ahead)).isoformat()
        return today.isoformat()
