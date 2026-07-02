"""
Role-Based Access Control (RBAC) engine.

Design rationale:
- Three roles: Admin > Manager > Employee, reflecting a typical corporate hierarchy.
- Permissions are granular (not just role checks) so the system can evolve to
  support custom role configurations without touching route code.
- RBAC is enforced server-side via FastAPI dependencies — never trust the client
  to assert its own permissions.
- Managers can read employee calendars (for scheduling) but cannot modify them.
  This reflects a common enterprise access pattern.
"""

from __future__ import annotations

from enum import Enum

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class Permission(str, Enum):
    READ_OWN_EMAIL = "read_own_email"
    SEND_EMAIL = "send_email"
    READ_OWN_CALENDAR = "read_own_calendar"
    WRITE_OWN_CALENDAR = "write_own_calendar"
    READ_EMPLOYEE_CALENDAR = "read_employee_calendar"
    SCHEDULE_MEETING = "schedule_meeting"
    MODIFY_ANY_MEETING = "modify_any_meeting"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_USERS = "manage_users"
    ACCESS_DIAGNOSTICS = "access_diagnostics"


# ---------------------------------------------------------------------------
# Permission matrix
# ---------------------------------------------------------------------------
# Every permission must be listed here for every role that holds it.
# Roles inherit nothing from each other — explicit is safer than implicit.

ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.EMPLOYEE: {
        Permission.READ_OWN_EMAIL,
        Permission.SEND_EMAIL,
        Permission.READ_OWN_CALENDAR,
        Permission.WRITE_OWN_CALENDAR,
        Permission.SCHEDULE_MEETING,
    },
    UserRole.MANAGER: {
        Permission.READ_OWN_EMAIL,
        Permission.SEND_EMAIL,
        Permission.READ_OWN_CALENDAR,
        Permission.WRITE_OWN_CALENDAR,
        Permission.READ_EMPLOYEE_CALENDAR,
        Permission.SCHEDULE_MEETING,
        Permission.VIEW_AUDIT_LOG,
    },
    UserRole.ADMIN: {p for p in Permission},  # All permissions
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Return True if *role* holds *permission*."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_role_from_token(token_data: dict) -> UserRole:
    """Extract and validate the UserRole from a decoded JWT payload."""
    raw_role = token_data.get("role", "employee")
    try:
        return UserRole(raw_role)
    except ValueError:
        return UserRole.EMPLOYEE


def check_resource_access(
    actor_role: UserRole,
    permission: Permission,
    actor_user_id: str,
    target_user_id: str,
) -> bool:
    """Check whether an actor may access another user's resource.

    For own-resource permissions (e.g. READ_OWN_EMAIL) the actor must be
    accessing their own resource.  For cross-user permissions (e.g.
    READ_EMPLOYEE_CALENDAR) the role check alone is sufficient.
    """
    if not has_permission(actor_role, permission):
        return False

    own_resource_permissions = {
        Permission.READ_OWN_EMAIL,
        Permission.SEND_EMAIL,
        Permission.READ_OWN_CALENDAR,
        Permission.WRITE_OWN_CALENDAR,
    }

    if permission in own_resource_permissions and actor_user_id != target_user_id:
        return False

    return True


# ---------------------------------------------------------------------------
# FastAPI dependency factory
# ---------------------------------------------------------------------------


def require_permission(permission: Permission):
    """Return a FastAPI dependency that enforces *permission*.

    Usage in a route:
        @router.get("/protected")
        async def route(_ = Depends(require_permission(Permission.READ_OWN_EMAIL))):
            ...
    """

    async def _check(current_user: dict = Depends(get_current_user)) -> None:
        role = get_role_from_token(current_user)
        if not has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Your role '{role.value}' does not have "
                    f"the '{permission.value}' permission required for this action."
                ),
            )

    return _check
