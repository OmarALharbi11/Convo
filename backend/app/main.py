"""
IPA — Intelligent Personal Assistant for Corporate Managers
FastAPI application entry point.

Middleware stack (outer → inner):
  TrustedHost → CORS → Request-ID/Timing → Routes

Exception handlers provide consistent JSON error envelopes.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import admin, audit, auth, calendar, email, voice
from app.core.config import get_settings
from app.integrations.graph.client import GraphAPIError, GraphAuthError, GraphPermissionError

# ---------------------------------------------------------------------------
# Structured logging bootstrap
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    settings = get_settings()
    log.info(
        "IPA starting up | env=%s | mock_mode=%s",
        settings.APP_ENV,
        settings.is_mock_mode,
    )
    # Ensure log directory exists
    import os
    os.makedirs("./logs", exist_ok=True)
    yield
    log.info("IPA shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="IPA — Intelligent Personal Assistant",
        description=(
            "Enterprise voice assistant for corporate managers. "
            "Integrates Microsoft 365 mail and calendar with AI-powered "
            "speech recognition and intent classification."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # Middleware
    # ------------------------------------------------------------------

    # 1. Trusted hosts
    trusted = ["localhost", "127.0.0.1"]
    if settings.ALLOWED_HOSTS:
        trusted.extend(h.strip() for h in settings.ALLOWED_HOSTS.split(",") if h.strip())
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted)

    # 2. CORS
    origins = [settings.FRONTEND_BASE_URL] if settings.FRONTEND_BASE_URL else []
    if settings.is_development:
        origins += ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # 3. Request ID + timing
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):  # type: ignore
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
        return response

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(auth.router)
    app.include_router(email.router)
    app.include_router(calendar.router)
    app.include_router(voice.router)
    app.include_router(audit.router)
    app.include_router(admin.router)

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = request.headers.get("x-request-id", "")
        errors = [
            {"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "validation_error", "details": errors, "request_id": request_id},
        )

    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        log.exception("Unhandled exception [%s]", request_id)

        if isinstance(exc, GraphAuthError):
            return JSONResponse(status_code=401, content={"error": "graph_auth_error",
                                "message": "Microsoft Graph authentication failed.", "request_id": request_id})
        if isinstance(exc, GraphPermissionError):
            return JSONResponse(status_code=403, content={"error": "graph_permission_error",
                                "message": "Insufficient Graph permissions.", "request_id": request_id})
        if isinstance(exc, GraphAPIError):
            return JSONResponse(status_code=502, content={"error": "graph_api_error",
                                "message": "Microsoft Graph API error.", "request_id": request_id})

        return JSONResponse(status_code=500, content={"error": "internal_server_error",
                            "message": "An unexpected error occurred.", "request_id": request_id})

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    @app.get("/api/health", tags=["System"], summary="Health check")
    async def health_check() -> dict[str, Any]:
        s = get_settings()
        return {
            "status": "ok",
            "version": "1.0.0",
            "mode": "mock" if s.is_mock_mode else "live",
            "env": s.APP_ENV,
        }

    return app


app = create_app()
