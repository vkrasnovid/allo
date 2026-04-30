from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CallStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    escalated = "escalated"
    missed = "missed"


class CallResult(str, Enum):
    booking_created = "booking_created"
    info_only = "info_only"
    escalated = "escalated"
    cancelled = "cancelled"
    no_action = "no_action"


class Call(BaseModel):
    """Звонок."""
    id: UUID
    tenant_id: UUID
    caller_phone: str
    client_id: Optional[UUID] = None
    did: str
    session_id: Optional[str] = None
    status: CallStatus = CallStatus.in_progress
    duration_sec: Optional[int] = None
    audio_key: Optional[str] = None
    transcript_text: Optional[str] = None
    result: Optional[CallResult] = None
    error_reason: Optional[str] = None


class CallCreate(BaseModel):
    """Создание записи о звонке."""
    tenant_id: UUID
    caller_phone: str
    did: str
    session_id: Optional[str] = None


class CallTranscript(BaseModel):
    """Фраза в расшифровке разговора."""
    id: UUID
    call_id: UUID
    speaker: str = Field(..., pattern="^(ai|client)$")
    text: str
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None
    tool_calls: Optional[dict] = None


class CallBookingLink(BaseModel):
    """Связь звонка и созданной записи."""
    call_id: UUID
    booking_id: UUID
