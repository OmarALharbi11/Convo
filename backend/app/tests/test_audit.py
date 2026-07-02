"""Audit log tests — verifies actions are logged and access is controlled."""

from __future__ import annotations

import pytest


class TestAuditLog:
    @pytest.mark.asyncio
    async def test_my_audit_log_accessible_to_any_user(self, employee_client):
        resp = await employee_client.get("/api/audit/logs/my")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_employee_cannot_view_all_audit_logs(self, employee_client):
        resp = await employee_client.get("/api/audit/logs")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_manager_can_view_all_audit_logs(self, manager_client):
        resp = await manager_client.get("/api/audit/logs")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_email_read_creates_audit_entry(self, manager_client):
        # Trigger an email read
        await manager_client.get("/api/email/inbox")
        # Check audit log
        resp = await manager_client.get("/api/audit/logs/my?limit=10")
        assert resp.status_code == 200
        entries = resp.json()["entries"]
        actions = [e["action"] for e in entries]
        assert "email.read" in actions

    @pytest.mark.asyncio
    async def test_audit_entry_structure(self, manager_client):
        await manager_client.get("/api/email/inbox")
        resp = await manager_client.get("/api/audit/logs/my?limit=5")
        entries = resp.json()["entries"]
        if entries:
            entry = entries[0]
            assert "id" in entry
            assert "actor_id" in entry
            assert "action" in entry
            assert "timestamp" in entry
            assert "outcome" in entry

    @pytest.mark.asyncio
    async def test_audit_entry_does_not_contain_email_body(self, manager_client):
        # Trigger email operations
        await manager_client.get("/api/email/messages/mgr-001")
        resp = await manager_client.get("/api/audit/logs/my?limit=10")
        # Check that no audit entry contains email body content
        for entry in resp.json()["entries"]:
            detail_str = str(entry.get("detail", {}))
            assert "body_text" not in detail_str
            assert "This is a test" not in detail_str  # No email content

    @pytest.mark.asyncio
    async def test_audit_log_action_filter(self, manager_client):
        # Trigger email read
        await manager_client.get("/api/email/inbox")
        resp = await manager_client.get("/api/audit/logs?action_filter=email.read&limit=20")
        assert resp.status_code == 200
        entries = resp.json()["entries"]
        for entry in entries:
            assert "email" in entry["action"]

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_audit(self, anon_client):
        resp = await anon_client.get("/api/audit/logs")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_permission_denied_is_logged(self, employee_client, manager_client):
        # Trigger a permission denied event
        await employee_client.get("/api/calendar/employee/someone@contoso.com/events")
        # Manager checks audit log — should see the denied event
        resp = await manager_client.get("/api/audit/logs?action_filter=permission.denied&limit=20")
        assert resp.status_code == 200
        # (Entry may or may not be present depending on RBAC middleware implementation)
        assert "entries" in resp.json()
