"""Admin router — diagnostics, user management."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.audit_logger import AuditAction, get_audit_logger
from app.core.config import get_settings
from app.core.rbac import Permission, UserRole, require_permission
from app.core.security import get_current_user
from app.integrations.stt.mock_provider import get_stt_provider
from app.integrations.tts.mock_provider import get_tts_provider
from app.intents.classifier import get_classifier
from app.schemas.audit import AuditLogQuery

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/diagnostics", summary="System diagnostics")
async def get_diagnostics(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.ACCESS_DIAGNOSTICS)),
) -> dict[str, Any]:
    settings = get_settings()
    audit_logger = get_audit_logger()
    recent = await audit_logger.query(AuditLogQuery(limit=10, offset=0))
    await audit_logger.log(AuditAction.ADMIN_ACCESS, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"endpoint": "GET /api/admin/diagnostics"})
    return {
        "app_env": settings.APP_ENV,
        "mock_mode": settings.is_mock_mode,
        "providers": {
            "stt": type(get_stt_provider()).__name__,
            "tts": type(get_tts_provider()).__name__,
            "intent_classifier": type(get_classifier()).__name__,
        },
        "feature_flags": {
            "USE_MOCK_GRAPH": settings.USE_MOCK_GRAPH,
            "USE_MOCK_STT": settings.USE_MOCK_STT,
            "USE_MOCK_TTS": settings.USE_MOCK_TTS,
            "USE_LLM_INTENT": settings.USE_LLM_INTENT,
        },
        "recent_audit_count": recent.total,
        "recent_entries": [e.model_dump(mode="json") for e in recent.entries[:5]],
    }
