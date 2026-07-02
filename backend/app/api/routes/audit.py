"""Audit log router — full trail (privileged) and own trail (any user)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.audit_logger import AuditAction, get_audit_logger
from app.core.rbac import Permission, require_permission
from app.core.security import get_current_user
from app.schemas.audit import AuditLogQuery, AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/logs", response_model=AuditLogResponse, summary="[Manager/Admin] Full audit trail")
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action_filter: str | None = Query(None),
    actor_filter: str | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.VIEW_AUDIT_LOG)),
) -> AuditLogResponse:
    audit_logger = get_audit_logger()
    result = await audit_logger.query(AuditLogQuery(
        limit=limit, offset=offset,
        action_filter=action_filter, actor_filter=actor_filter,
        since=since, until=until,
    ))
    await audit_logger.log(AuditAction.ADMIN_ACCESS, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"endpoint": "GET /api/audit/logs"})
    return result


@router.get("/logs/my", response_model=AuditLogResponse, summary="My own audit trail")
async def get_my_audit_logs(
    limit: int = Query(20, ge=1, le=100),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> AuditLogResponse:
    audit_logger = get_audit_logger()
    return await audit_logger.query(AuditLogQuery(
        limit=limit, offset=0, actor_filter=current_user["sub"]
    ))
