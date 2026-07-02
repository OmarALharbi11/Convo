"""RBAC unit and integration tests."""

from __future__ import annotations

import pytest

from app.core.rbac import ROLE_PERMISSIONS, Permission, UserRole, has_permission


class TestRBACMatrix:
    def test_admin_has_all_permissions(self):
        for perm in Permission:
            assert has_permission(UserRole.ADMIN, perm), f"Admin should have {perm}"

    def test_manager_can_read_employee_calendar(self):
        assert has_permission(UserRole.MANAGER, Permission.READ_EMPLOYEE_CALENDAR)

    def test_employee_cannot_read_employee_calendar(self):
        assert not has_permission(UserRole.EMPLOYEE, Permission.READ_EMPLOYEE_CALENDAR)

    def test_employee_can_read_own_email(self):
        assert has_permission(UserRole.EMPLOYEE, Permission.READ_OWN_EMAIL)

    def test_employee_can_send_email(self):
        assert has_permission(UserRole.EMPLOYEE, Permission.SEND_EMAIL)

    def test_employee_cannot_manage_users(self):
        assert not has_permission(UserRole.EMPLOYEE, Permission.MANAGE_USERS)

    def test_manager_cannot_manage_users(self):
        assert not has_permission(UserRole.MANAGER, Permission.MANAGE_USERS)

    def test_employee_cannot_access_diagnostics(self):
        assert not has_permission(UserRole.EMPLOYEE, Permission.ACCESS_DIAGNOSTICS)

    def test_manager_can_view_audit_log(self):
        assert has_permission(UserRole.MANAGER, Permission.VIEW_AUDIT_LOG)

    def test_employee_cannot_view_audit_log(self):
        assert not has_permission(UserRole.EMPLOYEE, Permission.VIEW_AUDIT_LOG)

    def test_manager_can_schedule_meeting(self):
        assert has_permission(UserRole.MANAGER, Permission.SCHEDULE_MEETING)

    def test_manager_cannot_modify_any_meeting(self):
        assert not has_permission(UserRole.MANAGER, Permission.MODIFY_ANY_MEETING)

    def test_admin_can_modify_any_meeting(self):
        assert has_permission(UserRole.ADMIN, Permission.MODIFY_ANY_MEETING)


class TestRBACRouteProtection:
    @pytest.mark.asyncio
    async def test_unauthenticated_inbox_returns_401(self, anon_client):
        resp = await anon_client.get("/api/email/inbox")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_unauthenticated_calendar_returns_401(self, anon_client):
        resp = await anon_client.get("/api/calendar/today")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_unauthenticated_voice_returns_401(self, anon_client):
        resp = await anon_client.post("/api/voice/command", json={"transcript": "test"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_employee_cannot_access_employee_calendar(self, employee_client):
        resp = await employee_client.get("/api/calendar/employee/someone@contoso.com/events")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_manager_can_access_employee_calendar(self, manager_client):
        resp = await manager_client.get("/api/calendar/employee/employee@contoso.com/events")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_employee_cannot_view_audit_logs(self, employee_client):
        resp = await employee_client.get("/api/audit/logs")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_manager_can_view_audit_logs(self, manager_client):
        resp = await manager_client.get("/api/audit/logs")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_employee_cannot_access_diagnostics(self, employee_client):
        resp = await employee_client.get("/api/admin/diagnostics")
        assert resp.status_code == 403
