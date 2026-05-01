"""Call ORM models — calls, transcripts, and call-booking links."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CallORM(Base):
    """Звонок."""

    __tablename__ = "calls"

    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'failed', 'escalated', 'missed')",
            name="ck_call_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    caller_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), index=True
    )
    did: Mapped[str] = mapped_column(String(20), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(30), default="in_progress",
    )
    duration_sec: Mapped[int | None] = mapped_column(Integer)
    audio_key: Mapped[str | None] = mapped_column(String(500))
    transcript_text: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(String(50))
    error_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, index=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant = relationship("TenantORM", back_populates="calls", foreign_keys=[tenant_id])
    transcripts = relationship("CallTranscriptORM", back_populates="call", cascade="all, delete-orphan")
    call_bookings = relationship("CallBookingORM", back_populates="call", cascade="all, delete-orphan")


class CallTranscriptORM(Base):
    """Фраза в расшифровке разговора."""

    __tablename__ = "call_transcripts"

    __table_args__ = (
        CheckConstraint(
            "speaker IN ('ai', 'client')",
            name="ck_transcript_speaker",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    speaker: Mapped[str] = mapped_column(
        String(10), nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_sec: Mapped[float | None] = mapped_column(Numeric(8, 3))
    end_sec: Mapped[float | None] = mapped_column(Numeric(8, 3))
    tool_calls: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )

    call = relationship("CallORM", back_populates="transcripts", foreign_keys=[call_id])


class CallBookingORM(Base):
    """M2M связь звонков и созданных записей."""

    __tablename__ = "call_bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint("call_id", "booking_id", name="unique_call_booking"),
    )

    call = relationship("CallORM", back_populates="call_bookings", foreign_keys=[call_id])
