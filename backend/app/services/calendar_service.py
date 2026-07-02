"""
Calendar service — business logic for calendar operations.

Maps between Graph adapter raw dicts and typed Pydantic schemas.
Handles free/busy analysis and conflict detection.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.calendar import (
    AvailabilityRequest,
    AvailabilityResponse,
    AvailabilitySlot,
    CalendarEvent,
    CalendarEventList,
    CreateEventRequest,
    UpdateEventRequest,
)


class CalendarService:
    def __init__(self, calendar_adapter) -> None:
        self._adapter = calendar_adapter

    async def get_events(
        self, user_email: str, start: datetime, end: datetime
    ) -> CalendarEventList:
        raw_events = await self._adapter.get_events(
            user_email=user_email, start=start, end=end
        )
        events = [self._map_event(e) for e in raw_events]
        return CalendarEventList(
            events=events,
            range_start=start,
            range_end=end,
            total=len(events),
        )

    async def create_event(
        self, user_email: str, request: CreateEventRequest
    ) -> CalendarEvent:
        raw = await self._adapter.create_event(
            user_email=user_email,
            subject=request.subject,
            start=request.start,
            end=request.end,
            attendees=request.attendees,
            location=request.location,
            description=request.description,
            is_online_meeting=request.is_online_meeting,
        )
        return self._map_event(raw)

    async def update_event(
        self, user_email: str, event_id: str, request: UpdateEventRequest
    ) -> CalendarEvent:
        updates: dict[str, Any] = {}
        if request.subject is not None:
            updates["subject"] = request.subject
        if request.start is not None:
            updates["start"] = request.start.isoformat()
        if request.end is not None:
            updates["end"] = request.end.isoformat()
        if request.attendees is not None:
            updates["attendees"] = request.attendees
        if request.location is not None:
            updates["location"] = request.location
        if request.description is not None:
            updates["description"] = request.description

        raw = await self._adapter.update_event(event_id=event_id, updates=updates)
        return self._map_event(raw)

    async def delete_event(self, user_email: str, event_id: str) -> None:
        await self._adapter.delete_event(event_id=event_id)

    async def check_availability(
        self, requester_email: str, request: AvailabilityRequest
    ) -> AvailabilityResponse:
        raw = await self._adapter.get_free_busy(
            attendee_emails=request.attendee_emails,
            start=request.start,
            end=request.end,
        )
        return self._parse_free_busy(request, raw)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_event(raw: dict[str, Any]) -> CalendarEvent:
        def _parse_dt(val: Any) -> datetime:
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                return datetime.fromisoformat(val)
            return datetime.now(timezone.utc)

        return CalendarEvent(
            event_id=str(raw.get("event_id", "")),
            subject=str(raw.get("subject", "(No Title)")),
            start=_parse_dt(raw.get("start")),
            end=_parse_dt(raw.get("end")),
            attendees=raw.get("attendees", []),
            organizer=str(raw.get("organizer", "")),
            location=str(raw.get("location", "")),
            description=str(raw.get("description", "")),
            is_online_meeting=bool(raw.get("is_online_meeting", False)),
            meeting_url=str(raw.get("meeting_url", "")),
            status=str(raw.get("status", "confirmed")),
        )

    @staticmethod
    def _parse_free_busy(
        request: AvailabilityRequest, raw: dict[str, Any]
    ) -> AvailabilityResponse:
        """Convert Graph scheduleInformation response to AvailabilityResponse."""
        schedule_items = raw.get("value", [])

        # Collect all busy intervals per attendee
        busy_map: dict[str, list[tuple[datetime, datetime]]] = {
            e: [] for e in request.attendee_emails
        }
        for schedule in schedule_items:
            email = schedule.get("scheduleId", "")
            for item in schedule.get("scheduleItems", []):
                try:
                    s = datetime.fromisoformat(item["start"])
                    e = datetime.fromisoformat(item["end"])
                    if email in busy_map:
                        busy_map[email].append((s, e))
                except (KeyError, ValueError):
                    pass

        # Generate 30-min slots across the requested range
        slots: list[AvailabilitySlot] = []
        current = request.start
        slot_duration = timedelta(minutes=request.duration_minutes)

        while current + slot_duration <= request.end:
            slot_end = current + slot_duration
            free: list[str] = []
            busy: list[str] = []
            for email, intervals in busy_map.items():
                is_busy = any(
                    not (slot_end <= b_start or current >= b_end)
                    for b_start, b_end in intervals
                )
                (busy if is_busy else free).append(email)

            slots.append(AvailabilitySlot(
                start=current,
                end=slot_end,
                is_available=len(busy) == 0,
                attendees_free=free,
                attendees_busy=busy,
            ))
            current += timedelta(minutes=30)

        suggested = [s for s in slots if s.is_available][:3]
        return AvailabilityResponse(
            requested_attendees=request.attendee_emails,
            slots=slots,
            suggested_times=suggested,
        )
