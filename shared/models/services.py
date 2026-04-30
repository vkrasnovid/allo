from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Service(BaseModel):
    """Услуга салона."""
    id: UUID
    tenant_id: UUID
    yclients_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    duration_min: int
    price_rub: Decimal
    category: Optional[str] = None
    is_active: bool = True


class ServiceCreate(BaseModel):
    """Создание новой услуги."""
    yclients_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    duration_min: int = Field(..., gt=0, le=480)
    price_rub: Decimal = Field(..., ge=0)
    category: Optional[str] = None
    is_active: bool = True


class ServiceUpdate(BaseModel):
    """Обновление услуги."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    duration_min: Optional[int] = Field(None, gt=0, le=480)
    price_rub: Optional[Decimal] = Field(None, ge=0)
    category: Optional[str] = None
    is_active: Optional[bool] = None
