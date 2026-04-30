"""Tool 2: get_masters — список мастеров."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from shared.tools.protocols import BookingServiceInterface, ToolDef, TOOL_REGISTRY


class GetMastersParams(BaseModel):
    service_id: Optional[str] = Field(
        None, description="ID услуги — показать только мастеров, которые делают эту услугу"
    )


class Master(BaseModel):
    id: str
    name: str = Field(description="Имя мастера")
    specialization: Optional[str] = Field(description="Специализация мастера")
    rating: Optional[float] = None


class GetMastersResult(BaseModel):
    masters: list[Master]


async def get_masters(
    tenant_id: UUID,
    params: GetMastersParams,
    booking_service: BookingServiceInterface,
) -> GetMastersResult:
    """
    Возвращает список мастеров.
    Если указан service_id — фильтрует по услуге.
    """
    service_uuid = UUID(params.service_id) if params.service_id else None
    raw_masters = await booking_service.get_masters(tenant_id, service_id=service_uuid)
    masters = [Master(**m) for m in raw_masters]
    return GetMastersResult(masters=masters)


TOOL_REGISTRY["get_masters"] = ToolDef(
    name="get_masters",
    description="Получить список мастеров. Можно отфильтровать по услуге.",
    params_schema=GetMastersParams.model_json_schema(),
    returns_schema=GetMastersResult.model_json_schema(),
)
