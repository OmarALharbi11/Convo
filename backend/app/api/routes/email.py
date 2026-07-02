"""Email router — inbox, message retrieval, summarisation, send, draft."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.audit_logger import AuditAction, get_audit_logger
from app.core.rbac import Permission, require_permission
from app.core.security import get_current_user
from app.integrations.graph.mock_adapter import get_mail_adapter
from app.schemas.email import (
    EmailFilter,
    EmailListResponse,
    EmailSummary,
    SendEmailRequest,
    SendEmailResponse,
)
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/email", tags=["Email"])


def _get_service(current_user: dict) -> EmailService:
    token = current_user.get("graph_access_token", "mock")
    return EmailService(mail_adapter=get_mail_adapter(graph_token=token))


@router.get("/inbox", response_model=EmailListResponse, summary="Fetch inbox messages")
async def get_inbox(
    limit: int = Query(10, ge=1, le=100),
    only_unread: bool = Query(False),
    folder: str = Query("inbox"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.READ_OWN_EMAIL)),
) -> EmailListResponse:
    audit_logger = get_audit_logger()
    service = _get_service(current_user)
    result = await service.get_inbox(
        user_email=current_user["email"],
        email_filter=EmailFilter(folder=folder, only_unread=only_unread, limit=limit),
    )
    await audit_logger.log(AuditAction.EMAIL_READ, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"folder": folder, "limit": limit})
    return result


@router.get("/messages/{message_id}", summary="Fetch a single email message")
async def get_message(
    message_id: str = Path(...),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.READ_OWN_EMAIL)),
) -> dict:
    service = _get_service(current_user)
    msg = await service.get_message(user_email=current_user["email"], message_id=message_id)
    return msg.model_dump(mode="json")


@router.get("/messages/{message_id}/summary", response_model=EmailSummary, summary="Summarise an email")
async def summarise_message(
    message_id: str = Path(...),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.READ_OWN_EMAIL)),
) -> EmailSummary:
    service = _get_service(current_user)
    return await service.summarise_message(user_email=current_user["email"], message_id=message_id)


@router.get("/summary/recent", response_model=list[EmailSummary], summary="Summarise recent emails")
async def summarise_recent(
    count: int = Query(5, ge=1, le=20),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.READ_OWN_EMAIL)),
) -> list[EmailSummary]:
    service = _get_service(current_user)
    return await service.summarise_recent(user_email=current_user["email"], count=count)


@router.post("/send", response_model=SendEmailResponse, status_code=status.HTTP_201_CREATED,
             summary="Send an email")
async def send_email(
    request: SendEmailRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.SEND_EMAIL)),
) -> SendEmailResponse:
    audit_logger = get_audit_logger()
    service = _get_service(current_user)
    result = await service.send_email(sender_email=current_user["email"], request=request)
    await audit_logger.log(AuditAction.EMAIL_SEND, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"to": request.to, "subject": request.subject, "message_id": result.message_id})
    return result


@router.post("/draft", response_model=SendEmailResponse, status_code=status.HTTP_201_CREATED,
             summary="Save email as draft")
async def create_draft(
    request: SendEmailRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.SEND_EMAIL)),
) -> SendEmailResponse:
    audit_logger = get_audit_logger()
    service = _get_service(current_user)
    result = await service.create_draft(sender_email=current_user["email"], request=request)
    await audit_logger.log(AuditAction.EMAIL_DRAFT, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"to": request.to, "subject": request.subject})
    return result
