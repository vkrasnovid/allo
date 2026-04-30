"""Tool 8: get_business_info — информация о салоне."""

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from shared.tools.protocols import BookingServiceInterface, ToolDef, TOOL_REGISTRY


class GetBusinessInfoParams(BaseModel):
    pass


class BusinessInfo(BaseModel):
    name: str
    address: Optional[str] = None
    phone: str
    work_hours: dict
    next_holiday: Optional[date] = None
    description: Optional[str] = None


class GetBusinessInfoResult(BaseModel):
    business: BusinessInfo


async def get_business_info(
    tenant_id: UUID,
    params: GetBusinessInfoParams,
    booking_service: BookingServiceInterface,
) -> GetBusinessInfoResult:
    """
    Возвращает информацию о салоне (адрес, часы работы, описание).
    """
    raw = await booking_service.get_business_info(tenant_id)
    return GetBusinessInfoResult(business=BusinessInfo(**raw))


TOOL_REGISTRY["get_business_info"] = ToolDef(
    name="get_business_info",
    description="Получить информацию о салоне (адрес, часы работы).",
    params_schema=GetBusinessInfoParams.model_json_schema(),
    returns_schema=GetBusinessInfoResult.model_json_schema(),
)
