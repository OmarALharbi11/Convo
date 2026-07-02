"""Calendar route integration tests."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone


class TestCalendarRoutes:
    @pytest.mark.asyncio
    async def test_get_today_returns_events(self, manager_client):
        resp = await manager_client.get("/api/calendar/today")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_week_returns_events(self, manager_client):
        resp = await manager_client.get("/api/calendar/week")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert len(data["events"]) > 0

    @pytest.mark.asyncio
    async def test_event_has_required_fields(self, manager_client):
        resp = await manager_client.get("/api/calendar/week")
        events = resp.json()["events"]
        assert len(events) > 0
        event = events[0]
        for field in ("event_id", "subject", "start", "end", "attendees"):
            assert field in event, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_create_event(self, manager_client):
        now = datetime.now(timezone.utc)
        resp = await manager_client.post("/api/calendar/events", json={
            "subject": "Test Meeting",
            "start": (now + timedelta(days=1, hours=10)).isoformat(),
            "end": (now + timedelta(days=1, hours=11)).isoformat(),
            "attendees": ["colleague@contoso.com"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["subject"] == "Test Meeting"
        assert "event_id" in data

    @pytest.mark.asyncio
    async def test_create_event_missing_subject_returns_422(self, manager_client):
        now = datetime.now(timezone.utc)
        resp = await manager_client.post("/api/calendar/events", json={
            "subject": "",
            "start": (now + timedelta(hours=1)).isoformat(),
            "end": (now + timedelta(hours=2)).isoformat(),
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_update_event(self, manager_client):
        resp = await manager_client.patch("/api/calendar/events/evt-001", json={
            "subject": "Updated Standup",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_event(self, manager_client):
        # First create an event to delete
        now = datetime.now(timezone.utc)
        create_resp = await manager_client.post("/api/calendar/events", json={
            "subject": "To Delete",
            "start": (now + timedelta(days=5)).isoformat(),
            "end": (now + timedelta(days=5, hours=1)).isoformat(),
        })
        event_id = create_resp.json()["event_id"]
        del_resp = await manager_client.delete(f"/api/calendar/events/{event_id}")
        assert del_resp.status_code == 204

    @pytest.mark.asyncio
    async def test_employee_cannot_access_employee_calendar(self, employee_client):
        resp = await employee_client.get("/api/calendar/employee/manager@contoso.com/events")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_manager_can_access_employee_calendar(self, manager_client):
        resp = await manager_client.get("/api/calendar/employee/employee@contoso.com/events")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_check_availability(self, manager_client):
        now = datetime.now(timezone.utc)
        resp = await manager_client.post("/api/calendar/availability", json={
            "attendee_emails": ["s.connor@contoso.com"],
            "start": now.isoformat(),
            "end": (now + timedelta(hours=8)).isoformat(),
            "duration_minutes": 30,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "slots" in data
        assert "suggested_times" in data
