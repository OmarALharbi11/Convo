"""Authentication route tests."""

from __future__ import annotations

import pytest


class TestMockLogin:
    @pytest.mark.asyncio
    async def test_mock_login_manager(self, anon_client):
        resp = await anon_client.post("/api/auth/mock-login", json={"role": "manager", "name": "Alex Chen"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_mock_login_employee(self, anon_client):
        resp = await anon_client.post("/api/auth/mock-login", json={"role": "employee", "name": "Jamie Lee"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_mock_login_admin(self, anon_client):
        resp = await anon_client.post("/api/auth/mock-login", json={"role": "admin", "name": "System Admin"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_mock_login_unknown_role_defaults_to_employee(self, anon_client):
        resp = await anon_client.post("/api/auth/mock-login", json={"role": "superuser", "name": "Test"})
        # Should succeed — unknown roles default to employee
        assert resp.status_code == 200


class TestGetMe:
    @pytest.mark.asyncio
    async def test_me_returns_user_info(self, manager_client):
        resp = await manager_client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        assert data["role"] == "manager"
        assert "permissions" in data
        assert len(data["permissions"]) > 0

    @pytest.mark.asyncio
    async def test_me_without_token_returns_401(self, anon_client):
        resp = await anon_client.get("/api/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_manager_has_employee_calendar_permission(self, manager_client):
        resp = await manager_client.get("/api/auth/me")
        permissions = resp.json()["permissions"]
        assert "read_employee_calendar" in permissions

    @pytest.mark.asyncio
    async def test_employee_lacks_employee_calendar_permission(self, employee_client):
        resp = await employee_client.get("/api/auth/me")
        permissions = resp.json()["permissions"]
        assert "read_employee_calendar" not in permissions

    @pytest.mark.asyncio
    async def test_employee_has_read_email_permission(self, employee_client):
        resp = await employee_client.get("/api/auth/me")
        assert "read_own_email" in resp.json()["permissions"]


class TestAuthStatus:
    @pytest.mark.asyncio
    async def test_auth_status_returns_config(self, anon_client):
        resp = await anon_client.get("/api/auth/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "mock_mode" in data
        assert data["mock_mode"] is True  # No Azure credentials in test env
        assert "app_env" in data
