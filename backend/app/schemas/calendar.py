"""Pydantic v2 schemas for calendar endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class CalendarEvent(BaseModel):
    event_id: str
    subject: str
    start: datetime
    end: datetime
    attendees: list[str] = []
    organizer: str = ""
    location: str = ""
    description: str = ""
    is_online_meeting: bool = False
    meeting_url: str = ""
    status: str = "confirmed"


class CalendarEventList(BaseModel):
    events: list[CalendarEvent]
    range_start: datetime
    range_end: datetime
    total: int


class CreateEventRequest(BaseModel):
    subject: str
    start: datetime
    end: datetime
    attendees: list[str] = []
    location: str = ""
    description: str = ""
    is_online_meeting: bool = False

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Event subject cannot be empty.")
        return v

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        if "start" in info.data and v <= info.data["start"]:
            raise ValueError("Event end time must be after start time.")
        return v


class UpdateEventRequest(BaseModel):
    subject: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    attendees: list[str] | None = None
    location: str | None = None
    description: str | None = None


class AvailabilityRequest(BaseModel):
    attendee_emails: list[str]
    start: datetime
    end: datetime
    duration_minutes: int = 30

    @field_validator("attendee_emails")
    @classmethod
    def at_least_one_attendee(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one attendee email is required.")
        return v


class AvailabilitySlot(BaseModel):
    start: datetime
    end: datetime
    is_available: bool
    attendees_free: list[str] = []
    attendees_busy: list[str] = []


class AvailabilityResponse(BaseModel):
    requested_attendees: list[str]
    slots: list[AvailabilitySlot]
    suggested_times: list[AvailabilitySlot]
