"""Tenant ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class TenantORM(Base, TimestampMixin):
    """Арендатор (салон красоты)."""

    __tablename__ = "tenants"

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended', 'deleted')",
            name="ck_tenant_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(String(1000))
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Moscow")
    status: Mapped[str] = mapped_column(
        String(20), default="active",
    )

    # Relationships
    services = relationship("ServiceORM", back_populates="tenant", cascade="all, delete-orphan")
    masters = relationship("MasterORM", back_populates="tenant", cascade="all, delete-orphan")
    clients = relationship("ClientORM", back_populates="tenant", cascade="all, delete-orphan")
    bookings = relationship("BookingORM", back_populates="tenant", cascade="all, delete-orphan")
    calls = relationship("CallORM", back_populates="tenant", cascade="all, delete-orphan")
    prompt_profiles = relationship("PromptProfileORM", back_populates="tenant", cascade="all, delete-orphan")
    notification_settings = relationship("NotificationSettingsORM", back_populates="tenant", uselist=False)
    sip_settings = relationship("SipSettingsORM", back_populates="tenant", uselist=False)
