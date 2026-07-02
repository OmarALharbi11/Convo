"""Intent and entity models for the hybrid classifier pipeline."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Intent(str, Enum):
    READ_EMAILS = "read_emails"
    SUMMARISE_EMAILS = "summarise_emails"
    SEND_EMAIL = "send_email"
    LIST_CALENDAR_EVENTS = "list_calendar_events"
    CHECK_AVAILABILITY = "check_availability"
    CREATE_MEETING = "create_meeting"
    MODIFY_MEETING = "modify_meeting"
    DELETE_MEETING = "delete_meeting"
    SHOW_EMPLOYEE_CALENDAR = "show_employee_calendar"
    READ_NOTIFICATIONS = "read_notifications"
    HELP = "help"
    REPEAT_LAST = "repeat_last_response"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    PERSON = "person"
    DATE = "date"
    TIME = "time"
    DURATION = "duration"
    EMAIL_SUBJECT = "email_subject"
    EMAIL_RECIPIENT = "email_recipient"
    MEETING_TITLE = "meeting_title"
    LOCATION = "location"
    EVENT_REFERENCE = "event_reference"
    FILTER_KEYWORD = "filter_keyword"


class ExtractedEntity(BaseModel):
    type: EntityType
    value: str
    raw_text: str
    confidence: float = 1.0


class ClassifiedIntent(BaseModel):
    intent: Intent
    entities: list[ExtractedEntity] = []
    confidence: float
    requires_confirmation: bool = False
    clarification_needed: bool = False
    clarification_question: str | None = None
    raw_input: str
    matched_pattern: str | None = None

    # High-risk intents that always require user confirmation
    HIGH_RISK_INTENTS: frozenset[Intent] = frozenset({
        Intent.SEND_EMAIL,
        Intent.CREATE_MEETING,
        Intent.MODIFY_MEETING,
        Intent.DELETE_MEETING,
    })

    def model_post_init(self, __context) -> None:
        if self.intent in self.HIGH_RISK_INTENTS:
            object.__setattr__(self, "requires_confirmation", True)

    model_config = {"arbitrary_types_allowed": True}
