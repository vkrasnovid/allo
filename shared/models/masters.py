from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Master(BaseModel):
    """Мастер салона."""
    id: UUID
    tenant_id: UUID
    yclients_id: Optional[int] = None
    name: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    is_active: bool = True


class MasterCreate(BaseModel):
    """Создание нового мастера."""
    yclients_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = None
    specialization: Optional[str] = None
    is_active: bool = True


class MasterUpdate(BaseModel):
    """Обновление мастера."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = None
    specialization: Optional[str] = None
    is_active: Optional[bool] = None


class MasterServiceLink(BaseModel):
    """Связь мастера и услуги."""
    master_id: UUID
    service_id: UUID
