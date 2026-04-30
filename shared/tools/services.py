"""Tool 1: get_services — список услуг салона."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from shared.tools.protocols import BookingServiceInterface, ToolDef, TOOL_REGISTRY


class GetServicesParams(BaseModel):
    category: Optional[str] = Field(
        None, description="Фильтр по категории: стрижки, окрашивание, маникюр, педикюр, уход"
    )


class Service(BaseModel):
    id: str
    name: str = Field(description="Название услуги")
    duration_min: int = Field(description="Длительность в минутах")
    price_rub: float = Field(description="Цена в рублях")
    category: Optional[str] = None
    description: Optional[str] = None


class GetServicesResult(BaseModel):
    services: list[Service]


async def get_services(
    tenant_id: UUID,
    params: GetServicesParams,
    booking_service: BookingServiceInterface,
) -> GetServicesResult:
    """
    Возвращает список услуг салона.
    Вызывается в начале диалога для показа списка.
    Может фильтроваться по категории.
    """
    raw_services = await booking_service.get_services(tenant_id, category=params.category)
    services = [Service(**s) for s in raw_services]
    return GetServicesResult(services=services)


TOOL_REGISTRY["get_services"] = ToolDef(
    name="get_services",
    description="Получить список услуг салона. Вызывай в начале, чтобы показать клиенту что есть.",
    params_schema=GetServicesParams.model_json_schema(),
    returns_schema=GetServicesResult.model_json_schema(),
)
