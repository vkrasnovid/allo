"""Tool 3: find_slots — поиск свободных временных слотов."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from shared.tools.protocols import BookingServiceInterface, ToolDef, TOOL_REGISTRY


class FindSlotsParams(BaseModel):
    master_id: Optional[str] = Field(
        None, description="ID мастера (если не указан — все мастера)"
    )
    service_id: Optional[str] = Field(
        None, description="ID услуги (для расчёта длительности)"
    )
    target_date: date = Field(
        default=None,
        description="Дата в формате YYYY-MM-DD",
        alias="date",
    )


class TimeSlot(BaseModel):
    start: datetime = Field(description="Начало слота (ISO 8601)")
    end: datetime = Field(description="Конец слота (ISO 8601)")
    master_id: str
    master_name: str


class FindSlotsResult(BaseModel):
    slots: list[TimeSlot]


async def find_slots(
    tenant_id: UUID,
    params: FindSlotsParams,
    booking_service: BookingServiceInterface,
) -> FindSlotsResult:
    """
    Ищет свободные временные слоты на указанную дату.
    Проверяет: внутренний календарь + существующие бронирования.
    Возвращает пустой список, если слотов нет.
    """
    master_uuid = UUID(params.master_id) if params.master_id else None
    service_uuid = UUID(params.service_id) if params.service_id else None
    raw_slots = await booking_service.find_slots(
        tenant_id,
        date=params.target_date,
        master_id=master_uuid,
        service_id=service_uuid,
    )
    slots = [TimeSlot(**s) for s in raw_slots]
    return FindSlotsResult(slots=slots)


TOOL_REGISTRY["find_slots"] = ToolDef(
    name="find_slots",
    description="Найти свободные слоты на определённую дату.",
    params_schema=FindSlotsParams.model_json_schema(by_alias=True),
    returns_schema=FindSlotsResult.model_json_schema(),
)
