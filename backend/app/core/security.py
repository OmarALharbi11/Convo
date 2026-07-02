"""
JWT security utilities — token creation, decoding, and FastAPI dependencies.

Design decisions:
- HS256 signing (symmetric) is appropriate for a single-service prototype.
  In production with multiple services, switch to RS256 (asymmetric).
- The Graph access token is embedded in the JWT payload so the backend can
  make Graph calls on behalf of the user without a separate session store.
  This is acceptable for a prototype; production systems should store tokens
  in a secure server-side session or cache (Redis) to avoid payload bloat
  and to allow token rotation.
- Token expiry defaults to 8 hours to match a typical working day.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Password helpers (used for any local credential storage, e.g. demo accounts)
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT containing *data*.

    The ``sub`` field is required and must be the user's unique identifier
    (Azure AD Object ID).  Additional claims (email, role, graph_access_token)
    are embedded for convenience.
    """
    settings = get_settings()
    if "sub" not in data:
        raise ValueError("JWT payload must contain a 'sub' claim.")

    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    return jwt.encode(
        payload,
        settings.APP_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT.  Raises HTTPException on any failure."""
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.APP_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """FastAPI dependency that extracts and validates the Bearer JWT.

    Returns the decoded token payload dict, which contains at minimum:
      - sub          (user ID / Azure OID)
      - email
      - display_name
      - role
      - graph_access_token
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


# Alias for clarity in route signatures
require_auth = get_current_user
