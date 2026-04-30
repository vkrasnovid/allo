"""Booking ORM model and history."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class BookingORM(Base, TimestampMixin):
    """Запись на услугу."""

    __tablename__ = "bookings"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'completed', 'cancelled', 'no_show')",
            name="ck_booking_status",
        ),
        CheckConstraint(
            "source IN ('phone', 'telegram', 'admin')",
            name="ck_booking_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    yclients_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True,
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    price_rub: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(
        String(20), default="phone",
    )

    # Relationships
    tenant = relationship("TenantORM", back_populates="bookings", foreign_keys=[tenant_id])
    client = relationship("ClientORM", back_populates="bookings", foreign_keys=[client_id])
    master = relationship("MasterORM", back_populates="bookings", foreign_keys=[master_id])
    history = relationship("BookingHistoryORM", back_populates="booking", cascade="all, delete-orphan")


class BookingHistoryORM(Base):
    """Аудит изменений статуса записи."""

    __tablename__ = "booking_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )

    booking = relationship("BookingORM", back_populates="history", foreign_keys=[booking_id])
