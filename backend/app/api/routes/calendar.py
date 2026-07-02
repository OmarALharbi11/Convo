"""Calendar router — events, availability, CRUD, employee calendar access."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import Response

from app.core.audit_logger import AuditAction, get_audit_logger
from app.core.rbac import Permission, require_permission
from app.core.security import get_current_user
from app.integrations.graph.mock_adapter import get_calendar_adapter
from app.schemas.calendar import (
    AvailabilityRequest,
    AvailabilityResponse,
    CalendarEvent,
    CalendarEventList,
    CreateEventRequest,
    UpdateEventRequest,
)
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


def _get_service(current_user: dict) -> CalendarService:
    token = current_user.get("graph_access_token", "mock")
    return CalendarService(calendar_adapter=get_calendar_adapter(graph_token=token))


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/events", response_model=CalendarEventList, summary="List events in time range")
async def get_events(
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.READ_OWN_CALENDAR)),
) -> CalendarEventList:
    service = _get_service(current_user)
    s = start or _now()
    e = end or (s + timedelta(days=7))
    return await service.get_events(user_email=current_user["email"], start=s, end=e)


@router.get("/today", response_model=CalendarEventList, summary="Today's events")
async def get_today(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.READ_OWN_CALENDAR)),
) -> CalendarEventList:
    service = _get_service(current_user)
    now = _now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    return await service.get_events(user_email=current_user["email"], start=start, end=end)


@router.get("/week", response_model=CalendarEventList, summary="Rolling 7-day window from today")
async def get_week(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.READ_OWN_CALENDAR)),
) -> CalendarEventList:
    service = _get_service(current_user)
    now = _now()
    week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    return await service.get_events(user_email=current_user["email"], start=week_start, end=week_end)


@router.get("/employee/{employee_email}/events", response_model=CalendarEventList,
            summary="[Manager] Read employee calendar")
async def get_employee_calendar(
    employee_email: str = Path(...),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.READ_EMPLOYEE_CALENDAR)),
) -> CalendarEventList:
    audit_logger = get_audit_logger()
    service = _get_service(current_user)
    s = start or _now()
    e = end or (s + timedelta(days=7))
    result = await service.get_events(user_email=employee_email, start=s, end=e)
    await audit_logger.log(AuditAction.CALENDAR_READ_EMPLOYEE, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           target_resource=employee_email,
                           details={"start": s.isoformat(), "end": e.isoformat()})
    return result


@router.post("/events", response_model=CalendarEvent, status_code=status.HTTP_201_CREATED,
             summary="Create calendar event")
async def create_event(
    request: CreateEventRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.WRITE_OWN_CALENDAR)),
) -> CalendarEvent:
    audit_logger = get_audit_logger()
    service = _get_service(current_user)
    event = await service.create_event(user_email=current_user["email"], request=request)
    await audit_logger.log(AuditAction.CALENDAR_EVENT_CREATED, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"event_id": event.event_id, "subject": event.subject})
    return event


@router.patch("/events/{event_id}", response_model=CalendarEvent, summary="Update calendar event")
async def update_event(
    event_id: str = Path(...),
    request: UpdateEventRequest = ...,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.WRITE_OWN_CALENDAR)),
) -> CalendarEvent:
    audit_logger = get_audit_logger()
    service = _get_service(current_user)
    event = await service.update_event(user_email=current_user["email"], event_id=event_id, request=request)
    await audit_logger.log(AuditAction.CALENDAR_EVENT_UPDATED, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"event_id": event_id})
    return event


@router.delete("/events/{event_id}", summary="Delete calendar event")
async def delete_event(
    event_id: str = Path(...),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.WRITE_OWN_CALENDAR)),
) -> Response:
    audit_logger = get_audit_logger()
    service = _get_service(current_user)
    await service.delete_event(user_email=current_user["email"], event_id=event_id)
    await audit_logger.log(AuditAction.CALENDAR_EVENT_DELETED, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"event_id": event_id})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/availability", response_model=AvailabilityResponse, summary="Check free/busy availability")
async def check_availability(
    request: AvailabilityRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    _: None = Depends(require_permission(Permission.READ_OWN_CALENDAR)),
) -> AvailabilityResponse:
    service = _get_service(current_user)
    return await service.check_availability(requester_email=current_user["email"], request=request)
