"""Tool 9: escalate_to_human — эскалация звонка живому человеку."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from shared.tools.protocols import BookingServiceInterface, ToolDef, TOOL_REGISTRY


class EscalateParams(BaseModel):
    call_id: str
    reason: str = Field(
        description="Причина эскалации: complaint, aggressive, complex_request, other"
    )
    client_summary: Optional[str] = Field(
        None, description="Краткое описание ситуации для администратора"
    )


class EscalateResult(BaseModel):
    action: str = "transfer"
    forward_to: str = Field(description="Номер для переадресации")
    transfer_initiated: bool


async def escalate_to_human(
    tenant_id: UUID,
    params: EscalateParams,
    booking_service: BookingServiceInterface,
) -> EscalateResult:
    """
    Эскалация звонка живому человеку.
    Инициирует forward на номер владельца.
    """
    result = await booking_service.escalate(tenant_id, data=params.model_dump())
    return EscalateResult(**result)


TOOL_REGISTRY["escalate_to_human"] = ToolDef(
    name="escalate_to_human",
    description="Перевести звонок на администратора. Используй при жалобах, агрессии или сложных запросах.",
    params_schema=EscalateParams.model_json_schema(),
    returns_schema=EscalateResult.model_json_schema(),
)
