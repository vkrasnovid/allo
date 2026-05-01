"""SIP settings ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SipSettingsORM(Base):
    """SIP-настройки тенанта."""

    __tablename__ = "sip_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    did: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    forward_number: Mapped[str | None] = mapped_column(String(20))
    sip_user: Mapped[str | None] = mapped_column(String(100))
    sip_password: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )

    tenant = relationship("TenantORM", back_populates="sip_settings", foreign_keys=[tenant_id])
