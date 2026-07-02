"""
Pytest configuration and shared fixtures for IPA backend tests.

All tests use the mock adapters (USE_MOCK_GRAPH=true by default) so no
Azure credentials or live APIs are required.
"""

from __future__ import annotations

import os
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-32-chars-minimum-!")
os.environ.setdefault("USE_MOCK_GRAPH", "true")
os.environ.setdefault("USE_MOCK_STT", "true")
os.environ.setdefault("USE_MOCK_TTS", "true")
os.environ.setdefault("USE_LLM_INTENT", "false")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,test")

from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
get_settings.cache_clear()  # Ensure env overrides above take effect before first call

from app.core.rbac import UserRole
from app.core.security import create_access_token
from app.main import app


def _make_token(user_id: str, email: str, name: str, role: UserRole) -> str:
    return create_access_token({
        "sub": user_id,
        "email": email,
        "display_name": name,
        "role": role.value,
        "graph_access_token": "mock_graph_token",
    }, expires_delta=timedelta(hours=8))


@pytest.fixture(scope="session")
def manager_token() -> str:
    return _make_token("mgr-001", "manager@contoso.com", "Test Manager", UserRole.MANAGER)


@pytest.fixture(scope="session")
def employee_token() -> str:
    return _make_token("emp-001", "employee@contoso.com", "Test Employee", UserRole.EMPLOYEE)


@pytest.fixture(scope="session")
def admin_token() -> str:
    return _make_token("adm-001", "admin@contoso.com", "Test Admin", UserRole.ADMIN)


@pytest_asyncio.fixture
async def manager_client(manager_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {manager_token}"
        yield client


@pytest_asyncio.fixture
async def employee_client(employee_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {employee_token}"
        yield client


@pytest_asyncio.fixture
async def admin_client(admin_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {admin_token}"
        yield client


@pytest_asyncio.fixture
async def anon_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
