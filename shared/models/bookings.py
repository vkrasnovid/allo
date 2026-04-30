from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class BookingSource(str, Enum):
    phone = "phone"
    telegram = "telegram"
    admin = "admin"


class Booking(BaseModel):
    """Запись на услугу."""
    id: UUID
    tenant_id: UUID
    client_id: UUID
    master_id: UUID
    service_id: UUID
    yclients_id: Optional[int] = None
    status: BookingStatus = BookingStatus.pending
    start_at: datetime
    end_at: datetime
    price_rub: Decimal
    comment: Optional[str] = None
    source: BookingSource = BookingSource.phone


class BookingCreate(BaseModel):
    """Создание новой записи."""
    client_phone: str = Field(..., description="Номер телефона клиента")
    client_name: Optional[str] = Field(None, description="Имя клиента")
    master_id: UUID
    service_id: UUID
    start_at: datetime
    comment: Optional[str] = None
    source: BookingSource = BookingSource.phone


class BookingUpdate(BaseModel):
    """Обновление записи (перенос, смена услуги/мастера, отмена)."""
    action: str = Field(..., pattern="^(reschedule|update_service|update_master|cancel)$")
    start_at: Optional[datetime] = None
    master_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    reason: Optional[str] = None
    comment: Optional[str] = None


class BookingInfo(BaseModel):
    """Краткая информация о записи (для списков)."""
    booking_id: UUID
    service_name: str
    master_name: str
    client_name: Optional[str] = None
    client_phone: str
    start_at: datetime
    end_at: datetime
    status: BookingStatus
    price_rub: Decimal


class BookingHistoryEntry(BaseModel):
    """Запись в истории изменений статуса."""
    id: UUID
    booking_id: UUID
    from_status: Optional[str] = None
    to_status: str
    changed_by: str
    reason: Optional[str] = None
    created_at: datetime
