"""
Authentication router — Microsoft OAuth 2.0 (MSAL) + mock-login for development.

GET  /api/auth/login        → redirect to Microsoft authorization endpoint
GET  /api/auth/callback     → exchange code, mint JWT, redirect to frontend
POST /api/auth/logout       → audit log logout
GET  /api/auth/me           → current user info + permissions
GET  /api/auth/status       → diagnostic/configuration info
POST /api/auth/mock-login   → DEV ONLY — JWT for synthetic user
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.core.audit_logger import AuditAction, get_audit_logger
from app.core.config import get_settings
from app.core.rbac import Permission, UserRole, has_permission
from app.core.security import create_access_token, get_current_user
from app.schemas.auth import TokenResponse, UserInfo

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-process OAuth state store (use Redis in production)
_pending_states: dict[str, dict[str, Any]] = {}

_GRAPH_SCOPES = [
    "User.Read",
    "Mail.Read",
    "Mail.Send",
    "Calendars.ReadWrite",
    "offline_access",
]


def _role_from_email(email: str, settings) -> UserRole:
    manager_list = [e.strip().lower() for e in (settings.MANAGER_EMAILS or "").split(",") if e.strip()]
    admin_list = [e.strip().lower() for e in (settings.ADMIN_EMAILS or "").split(",") if e.strip()]
    el = email.lower()
    if el in admin_list:
        return UserRole.ADMIN
    if el in manager_list:
        return UserRole.MANAGER
    return UserRole.EMPLOYEE


def _permissions_for_role(role: UserRole) -> list[str]:
    return [p.value for p in Permission if has_permission(role, p)]


@router.get("/login", summary="Initiate Microsoft OAuth 2.0 login")
async def login() -> RedirectResponse:
    settings = get_settings()

    if not settings.AZURE_CLIENT_ID:
        # Mock mode — skip real OAuth
        mock_state = secrets.token_urlsafe(32)
        _pending_states[mock_state] = {"mock": True, "created_at": datetime.now(timezone.utc).timestamp()}
        redirect_url = f"{settings.BACKEND_BASE_URL}/api/auth/callback?code=mock_code&state={mock_state}"
        return RedirectResponse(url=redirect_url, status_code=302)

    import msal  # noqa: PLC0415
    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.AZURE_CLIENT_ID,
        client_credential=settings.AZURE_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}",
    )
    state = secrets.token_urlsafe(32)
    flow = msal_app.initiate_auth_code_flow(
        scopes=_GRAPH_SCOPES,
        redirect_uri=f"{settings.BACKEND_BASE_URL}/api/auth/callback",
        state=state,
    )
    _pending_states[state] = {"flow": flow, "created_at": datetime.now(timezone.utc).timestamp()}
    auth_uri = flow.get("auth_uri", "")
    if not auth_uri:
        raise HTTPException(status_code=502, detail="Failed to build Microsoft authorization URL.")
    return RedirectResponse(url=auth_uri, status_code=302)


@router.get("/callback", summary="Microsoft OAuth 2.0 callback")
async def callback(code: str = Query(...), state: str = Query(...)) -> RedirectResponse:
    settings = get_settings()
    audit_logger = get_audit_logger()
    pending = _pending_states.pop(state, None)

    if pending is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")

    if pending.get("mock") or not settings.AZURE_CLIENT_ID:
        mock_id = str(uuid.uuid4())
        email = "manager@contoso.com"
        role = UserRole.MANAGER
        token = create_access_token({
            "sub": mock_id, "email": email, "display_name": "Demo Manager",
            "role": role.value, "graph_access_token": "mock_graph_token",
        })
        await audit_logger.log(AuditAction.AUTH_LOGIN, actor_id=mock_id, actor_email=email,
                               actor_role=role.value, details={"mode": "mock"})
        return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/auth/callback?token={token}", status_code=302)

    import msal  # noqa: PLC0415
    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.AZURE_CLIENT_ID,
        client_credential=settings.AZURE_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}",
    )
    try:
        result = msal_app.acquire_token_by_auth_code_flow(
            auth_code_flow=pending["flow"],
            auth_response={"code": code, "state": state},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {exc}") from exc

    if "error" in result:
        raise HTTPException(status_code=401, detail=result.get("error_description", "Auth failed."))

    claims = result.get("id_token_claims", {})
    oid = claims.get("oid", str(uuid.uuid4()))
    email = claims.get("preferred_username") or claims.get("email") or "unknown@unknown.com"
    display_name = claims.get("name", email.split("@")[0])
    graph_token = result.get("access_token", "")
    role = _role_from_email(email, settings)

    token = create_access_token({
        "sub": oid, "email": email, "display_name": display_name,
        "role": role.value, "graph_access_token": graph_token,
    })
    await audit_logger.log(AuditAction.AUTH_LOGIN, actor_id=oid, actor_email=email,
                           actor_role=role.value, details={"display_name": display_name})
    return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/auth/callback?token={token}", status_code=302)


@router.post("/logout", summary="Logout current user")
async def logout(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    audit_logger = get_audit_logger()
    await audit_logger.log(AuditAction.AUTH_LOGOUT, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""))
    return {"status": "logged_out"}


@router.get("/me", response_model=UserInfo, summary="Current user info and permissions")
async def get_me(current_user: Annotated[dict, Depends(get_current_user)]) -> UserInfo:
    role = UserRole(current_user.get("role", "employee"))
    return UserInfo(
        user_id=current_user["sub"],
        email=current_user.get("email", ""),
        display_name=current_user.get("display_name", ""),
        role=role,
        permissions=_permissions_for_role(role),
    )


@router.get("/status", summary="Auth configuration diagnostic")
async def auth_status() -> dict:
    settings = get_settings()
    return {
        "mock_mode": not bool(settings.AZURE_CLIENT_ID),
        "tenant_configured": bool(settings.AZURE_TENANT_ID),
        "client_configured": bool(settings.AZURE_CLIENT_ID),
        "scopes": _GRAPH_SCOPES,
        "app_env": settings.APP_ENV,
    }


class _MockLoginBody(BaseModel):
    role: str = "manager"
    name: str = "Test User"


@router.post("/mock-login", response_model=TokenResponse, summary="[DEV ONLY] Obtain JWT for synthetic user")
async def mock_login(body: _MockLoginBody) -> TokenResponse:
    settings = get_settings()
    if settings.APP_ENV != "development":
        raise HTTPException(status_code=404, detail="Not available in this environment.")

    role_map = {"manager": UserRole.MANAGER, "employee": UserRole.EMPLOYEE, "admin": UserRole.ADMIN}
    role = role_map.get(body.role.lower(), UserRole.EMPLOYEE)
    mock_id = str(uuid.uuid4())
    email = f"{body.name.lower().replace(' ', '.')}@dev.local"

    token = create_access_token({
        "sub": mock_id, "email": email, "display_name": body.name,
        "role": role.value, "graph_access_token": "mock_graph_token_dev",
    })
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
