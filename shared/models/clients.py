"""Client Pydantic models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Client(BaseModel):
    """Клиент салона."""
    id: UUID
    tenant_id: UUID
    phone: str
    name: Optional[str] = None
    total_visits: int = 0
    last_visit_at: Optional[datetime] = None
    preferences: dict = {}


class ClientCreate(BaseModel):
    """Создание нового клиента."""
    tenant_id: UUID
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    name: Optional[str] = None


class ClientUpdate(BaseModel):
    """Обновление клиента."""
    name: Optional[str] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")


class ClientInfo(BaseModel):
    """Информация о клиенте (с историей)."""
    id: UUID
    tenant_id: UUID
    phone: str
    name: Optional[str] = None
    total_visits: int = 0
    last_visit_at: Optional[datetime] = None
    preferences: dict = {}
    preferred_master_id: Optional[str] = None
    preferred_master_name: Optional[str] = None
    preferred_services: list[str] = []
