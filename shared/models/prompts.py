from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PromptBlock(BaseModel):
    """Блок промпта."""
    id: UUID
    profile_id: UUID
    block_key: str
    content: str
    position: int = 0
    is_active: bool = True


class PromptBlockCreate(BaseModel):
    """Создание блока промпта."""
    block_key: str = Field(..., pattern="^(greeting|tone|business_info|services|masters|rules|farewell)$")
    content: str
    position: int = 0
    is_active: bool = True


class PromptProfile(BaseModel):
    """Профиль промпта."""
    id: UUID
    tenant_id: UUID
    name: str
    is_active: bool = True
    blocks: list[PromptBlock] = []


class PromptProfileCreate(BaseModel):
    """Создание профиля промпта."""
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    blocks: list[PromptBlockCreate] = []


class ComposedPrompt(BaseModel):
    """Собранный промпт (базовый + блоки + контекст)."""
    system_prompt: str
    blocks_used: list[str]
    client_context: Optional[dict] = None
