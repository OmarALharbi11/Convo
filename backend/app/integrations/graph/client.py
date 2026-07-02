"""
Microsoft Graph API HTTP client with typed error mapping.

The adapter pattern is used so:
1. Live Graph calls can be swapped for mock adapters in tests/demo mode.
2. All Graph HTTP errors map to typed exceptions that routes can handle cleanly.
3. Token management is centralised here — routes never touch raw HTTP.
"""

from __future__ import annotations

from typing import Any

import httpx



class GraphAPIError(Exception):
    """Base class for all Microsoft Graph errors."""

    def __init__(self, message: str, status_code: int = 0, graph_code: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.graph_code = graph_code


class GraphAuthError(GraphAPIError):
    """401 — token invalid or expired."""


class GraphPermissionError(GraphAPIError):
    """403 — insufficient scopes or consent not granted."""


class GraphNotFoundError(GraphAPIError):
    """404 — resource does not exist."""


class GraphRateLimitError(GraphAPIError):
    """429 — throttled by Graph."""


class GraphConflictError(GraphAPIError):
    """409 — scheduling conflict or duplicate resource."""


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


class GraphClient:
    """Async HTTP client for Microsoft Graph v1.0.

    Each instance is bound to a single user's delegated access token.
    Instantiate per-request (the token is short-lived).
    """

    BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, access_token: str) -> None:
        self._token = access_token
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    async def __aenter__(self) -> "GraphClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._client.aclose()

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Core HTTP verbs
    # ------------------------------------------------------------------

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self._client.get(path, params=params)
        return self._handle(response)

    async def post(self, path: str, json_data: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self._client.post(path, json=json_data or {})
        return self._handle(response)

    async def patch(self, path: str, json_data: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.patch(path, json=json_data)
        return self._handle(response)

    async def delete(self, path: str) -> None:
        response = await self._client.delete(path)
        if response.status_code not in (200, 204):
            self._handle(response)

    # ------------------------------------------------------------------
    # Error mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _handle(response: httpx.Response) -> dict[str, Any]:
        if response.is_success:
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()

        # Attempt to extract Graph error code from response body
        graph_code = ""
        try:
            body = response.json()
            graph_code = body.get("error", {}).get("code", "")
            message = body.get("error", {}).get("message", response.text)
        except Exception:
            message = response.text

        sc = response.status_code
        if sc == 401:
            raise GraphAuthError(message, status_code=sc, graph_code=graph_code)
        if sc == 403:
            raise GraphPermissionError(message, status_code=sc, graph_code=graph_code)
        if sc == 404:
            raise GraphNotFoundError(message, status_code=sc, graph_code=graph_code)
        if sc == 409:
            raise GraphConflictError(message, status_code=sc, graph_code=graph_code)
        if sc == 429:
            raise GraphRateLimitError(message, status_code=sc, graph_code=graph_code)
        raise GraphAPIError(message, status_code=sc, graph_code=graph_code)
