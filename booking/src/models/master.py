"""Master ORM model and M2M link table."""

import uuid

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class MasterORM(Base, TimestampMixin):
    """Мастер салона."""

    __tablename__ = "masters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    yclients_id: Mapped[int | None] = mapped_column()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    specialization: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    tenant = relationship("TenantORM", back_populates="masters", foreign_keys=[tenant_id])
    master_services = relationship("MasterServiceORM", back_populates="master", cascade="all, delete-orphan")
    bookings = relationship("BookingORM", back_populates="master", foreign_keys="BookingORM.master_id")


class MasterServiceORM(Base):
    """M2M связь мастеров и услуг."""

    __tablename__ = "master_services"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint("master_id", "service_id", name="unique_master_service"),
    )

    master = relationship("MasterORM", back_populates="master_services", foreign_keys=[master_id])
    service = relationship("ServiceORM", back_populates="master_services", foreign_keys=[service_id])
