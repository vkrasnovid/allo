"""Pydantic schemas for the booking API — request/response models."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ===== Slots =====

class SlotRequest(BaseModel):
    master_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    date: date
    days: int = Field(default=1, ge=1, le=14)


class SlotResponse(BaseModel):
    start: datetime
    end: datetime
    master_id: UUID
    master_name: str


class SlotsListResponse(BaseModel):
    slots: list[SlotResponse]


# ===== Bookings =====

class BookingCreateRequest(BaseModel):
    client_phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    client_name: Optional[str] = None
    master_id: UUID
    service_id: UUID
    start_at: datetime
    comment: Optional[str] = None
    source: str = "phone"


class BookingUpdateRequest(BaseModel):
    action: str = Field(..., pattern=r"^(reschedule|update_service|update_master|cancel)$")
    start_at: Optional[datetime] = None
    master_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    reason: Optional[str] = None
    comment: Optional[str] = None


class BookingResponse(BaseModel):
    booking_id: UUID
    status: str
    summary: str
    yclients_id: Optional[int] = None
    client: Optional[dict] = None
    master: Optional[dict] = None
    service: Optional[dict] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class BookingListResponse(BaseModel):
    bookings: list[dict]


class CancelResponse(BaseModel):
    booking_id: UUID
    status: str = "cancelled"
    cancelled_at: datetime
    penalty_info: Optional[str] = None


# ===== Clients =====

class ClientByPhoneResponse(BaseModel):
    client: Optional[dict] = None
    last_booking: Optional[dict] = None
    error: Optional[str] = None


# ===== Business Info =====

class BusinessInfoResponse(BaseModel):
    tenant_name: str
    address: Optional[str] = None
    phone: str
    work_hours: dict
    next_holiday: Optional[date] = None
    description: Optional[str] = None


# ===== Escalation =====

class EscalateRequest(BaseModel):
    call_id: str
    reason: str
    client_summary: Optional[str] = None


class EscalateResponse(BaseModel):
    forward_to: str
    action: str = "transfer"


# ===== Common =====

class ErrorResponse(BaseModel):
    error: str
    message: str
