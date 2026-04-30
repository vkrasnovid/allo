from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class WorkHours(BaseModel):
    """Рабочие часы салона по дням недели."""
    mon_fri: str = Field(default="09:00-21:00", alias="mon-fri")
    sat: str = Field(default="10:00-20:00")
    sun: str = Field(default="10:00-18:00")


class TenantInfo(BaseModel):
    """Информация о тенанте (салоне)."""
    id: UUID
    name: str
    slug: str
    phone: str
    timezone: str = "Europe/Moscow"
    address: Optional[str] = None
    description: Optional[str] = None
    work_hours: WorkHours = Field(default_factory=WorkHours)
    next_holiday: Optional[date] = None
    status: str = "active"


class BusinessInfo(BaseModel):
    """Публичная информация о салоне (для tools)."""
    name: str
    address: Optional[str] = None
    phone: str
    work_hours: WorkHours
    next_holiday: Optional[date] = None
    description: Optional[str] = None


class SipSettings(BaseModel):
    """SIP-настройки тенанта."""
    id: UUID
    tenant_id: UUID
    did: str
    forward_number: Optional[str] = None
    is_active: bool = True


class NotificationSettings(BaseModel):
    """Настройки уведомлений."""
    id: UUID
    tenant_id: UUID
    telegram_chat_id: Optional[str] = None
    sms_enabled: bool = True
    reminder_day: bool = True
    reminder_hour: bool = True
