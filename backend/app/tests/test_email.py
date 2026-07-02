"""Email route integration tests."""

from __future__ import annotations

import pytest


class TestEmailRoutes:
    @pytest.mark.asyncio
    async def test_get_inbox_returns_messages(self, manager_client):
        resp = await manager_client.get("/api/email/inbox")
        assert resp.status_code == 200
        data = resp.json()
        assert "messages" in data
        assert len(data["messages"]) > 0
        assert "total" in data

    @pytest.mark.asyncio
    async def test_inbox_message_has_required_fields(self, manager_client):
        resp = await manager_client.get("/api/email/inbox")
        msg = resp.json()["messages"][0]
        for field in ("id", "subject", "sender_name", "sender_email", "is_read", "preview"):
            assert field in msg, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_get_inbox_unread_filter(self, manager_client):
        resp = await manager_client.get("/api/email/inbox?only_unread=true")
        assert resp.status_code == 200
        messages = resp.json()["messages"]
        assert all(not m["is_read"] for m in messages)

    @pytest.mark.asyncio
    async def test_inbox_limit_parameter(self, manager_client):
        resp = await manager_client.get("/api/email/inbox?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()["messages"]) <= 2

    @pytest.mark.asyncio
    async def test_summarise_recent_emails(self, manager_client):
        resp = await manager_client.get("/api/email/summary/recent?count=3")
        assert resp.status_code == 200
        summaries = resp.json()
        assert len(summaries) <= 3
        for s in summaries:
            assert "summary_text" in s
            assert "urgency_level" in s
            assert s["urgency_level"] in ("high", "medium", "low")

    @pytest.mark.asyncio
    async def test_get_message_by_id(self, manager_client):
        resp = await manager_client.get("/api/email/messages/mgr-001")
        assert resp.status_code == 200
        assert resp.json()["id"] == "mgr-001"

    @pytest.mark.asyncio
    async def test_send_email_success(self, manager_client):
        resp = await manager_client.post("/api/email/send", json={
            "to": ["colleague@contoso.com"],
            "subject": "Test Email",
            "body": "This is a test email sent via IPA.",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "message_id" in data
        assert data["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_email_empty_recipient_returns_422(self, manager_client):
        resp = await manager_client.post("/api/email/send", json={
            "to": [],
            "subject": "Test",
            "body": "Body",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_send_email_empty_subject_returns_422(self, manager_client):
        resp = await manager_client.post("/api/email/send", json={
            "to": ["someone@contoso.com"],
            "subject": "",
            "body": "Body",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_employee_can_read_own_inbox(self, employee_client):
        resp = await employee_client.get("/api/email/inbox")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_read_email(self, anon_client):
        resp = await anon_client.get("/api/email/inbox")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_draft(self, manager_client):
        resp = await manager_client.post("/api/email/draft", json={
            "to": ["someone@contoso.com"],
            "subject": "Draft Subject",
            "body": "Draft body text.",
        })
        assert resp.status_code == 201
        assert resp.json()["status"] == "draft"
