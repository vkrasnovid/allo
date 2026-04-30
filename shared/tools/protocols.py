"""Tool interfaces, registry, and data models for shared tools library."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Protocol
from uuid import UUID

from pydantic import BaseModel, Field


class BookingServiceInterface(Protocol):
    """Interface for booking service client injected into tools."""

    async def get_services(self, tenant_id: UUID, category: Optional[str] = None) -> list[dict]: ...

    async def get_masters(self, tenant_id: UUID, service_id: Optional[UUID] = None) -> list[dict]: ...

    async def find_slots(
        self,
        tenant_id: UUID,
        date: date,
        master_id: Optional[UUID] = None,
        service_id: Optional[UUID] = None,
    ) -> list[dict]: ...

    async def create_booking(self, tenant_id: UUID, data: dict) -> dict: ...

    async def find_bookings(
        self,
        tenant_id: UUID,
        client_phone: str,
        status: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]: ...

    async def update_booking(
        self,
        tenant_id: UUID,
        booking_id: UUID,
        data: dict,
    ) -> dict: ...

    async def cancel_booking(
        self,
        tenant_id: UUID,
        booking_id: UUID,
        reason: str,
        comment: Optional[str] = None,
    ) -> dict: ...

    async def get_business_info(self, tenant_id: UUID) -> dict: ...

    async def escalate(self, tenant_id: UUID, data: dict) -> dict: ...

    async def get_or_create_client(self, tenant_id: UUID, phone: str, name: Optional[str] = None) -> dict: ...


class ToolDef(BaseModel):
    """Definition of a tool with its schema."""
    name: str
    description: str
    params_schema: dict
    returns_schema: dict


TOOL_REGISTRY: dict[str, ToolDef] = {}
