"""Tenant isolation middleware for FastAPI."""

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class TenantContext:
    """Request-scoped tenant context."""
    tenant_id: UUID
    name: str = ""
    timezone: str = "Europe/Moscow"
    settings: dict = field(default_factory=dict)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Извлекает tenant_id из:
    1. Path /api/v1/tenants/{tenant_id}/...
    2. X-Tenant-ID header (для внутренних сервисов)
    3. JWT токена (для admin панели) — future
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = self._extract_tenant_id(request)
        if not tenant_id:
            return JSONResponse(
                status_code=401,
                content={"error": "TENANT_REQUIRED", "message": "Tenant ID is required"},
            )

        # В MVP проверка существования tenant может быть пропущена
        # для упрощения; в production нужно проверить статус tenant
        request.state.tenant = TenantContext(tenant_id=tenant_id)
        return await call_next(request)

    def _extract_tenant_id(self, request: Request) -> Optional[UUID]:
        # 1. Path parameter
        tenant_id_str = request.path_params.get("tenant_id")
        if tenant_id_str:
            try:
                return UUID(tenant_id_str)
            except ValueError:
                pass

        # 2. Header
        tenant_id_str = request.headers.get("X-Tenant-ID")
        if tenant_id_str:
            try:
                return UUID(tenant_id_str)
            except ValueError:
                pass

        return None
