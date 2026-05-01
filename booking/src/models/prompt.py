"""Prompt profile ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PromptProfileORM(Base):
    """Профиль промпта."""

    __tablename__ = "prompt_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="unique_tenant_profile_name"),
    )

    tenant = relationship("TenantORM", back_populates="prompt_profiles", foreign_keys=[tenant_id])
    blocks = relationship("PromptBlockORM", back_populates="profile", cascade="all, delete-orphan")


class PromptBlockORM(Base):
    """Блок промпта."""

    __tablename__ = "prompt_blocks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    block_key: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )

    __table_args__ = (
        UniqueConstraint("profile_id", "block_key", name="unique_profile_block_key"),
    )

    profile = relationship("PromptProfileORM", back_populates="blocks", foreign_keys=[profile_id])
