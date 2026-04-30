"""Tools 4, 5, 6, 7: create_booking, find_booking, update_booking, cancel_booking."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from shared.tools.protocols import BookingServiceInterface, ToolDef, TOOL_REGISTRY


# ===== Tool 4: create_booking =====

class CreateBookingParams(BaseModel):
    client_phone: str = Field(description="Номер телефона клиента в формате +7...")
    client_name: str = Field(description="Имя клиента")
    master_id: str = Field(description="ID мастера")
    service_id: str = Field(description="ID услуги")
    start_at: datetime = Field(description="Дата и время начала в ISO 8601")
    comment: Optional[str] = Field(None, description="Комментарий клиента")


class CreateBookingResult(BaseModel):
    booking_id: str
    status: str = Field(description="confirmed | pending")
    yclients_id: Optional[int] = None
    summary: str = Field(description="Человекочитаемое описание записи")


async def create_booking(
    tenant_id: UUID,
    params: CreateBookingParams,
    booking_service: BookingServiceInterface,
) -> CreateBookingResult:
    """
    Создаёт запись на услугу.
    """
    result = await booking_service.create_booking(tenant_id, data=params.model_dump())
    return CreateBookingResult(**result)


TOOL_REGISTRY["create_booking"] = ToolDef(
    name="create_booking",
    description="Создать запись клиента на услугу. Вызывай, когда клиент согласился на время.",
    params_schema=CreateBookingParams.model_json_schema(),
    returns_schema=CreateBookingResult.model_json_schema(),
)


# ===== Tool 5: find_booking =====

class FindBookingParams(BaseModel):
    client_phone: str = Field(description="Номер телефона клиента")
    status: Optional[str] = Field(None, description="Фильтр по статусу")
    limit: int = Field(5, description="Максимум записей", ge=1, le=50)


class BookingInfo(BaseModel):
    booking_id: str
    service_name: str
    master_name: str
    start_at: datetime
    status: str
    price_rub: float


class FindBookingResult(BaseModel):
    bookings: list[BookingInfo]


async def find_booking(
    tenant_id: UUID,
    params: FindBookingParams,
    booking_service: BookingServiceInterface,
) -> FindBookingResult:
    """
    Ищет существующие записи клиента по номеру телефона.
    Используется при переносе/отмене/повторном звонке.
    """
    raw_bookings = await booking_service.find_bookings(
        tenant_id,
        client_phone=params.client_phone,
        status=params.status,
        limit=params.limit,
    )
    bookings = [BookingInfo(**b) for b in raw_bookings]
    return FindBookingResult(bookings=bookings)


TOOL_REGISTRY["find_booking"] = ToolDef(
    name="find_booking",
    description="Найти существующие записи клиента по номеру телефона.",
    params_schema=FindBookingParams.model_json_schema(),
    returns_schema=FindBookingResult.model_json_schema(),
)


# ===== Tool 6: update_booking =====

class UpdateBookingParams(BaseModel):
    booking_id: str = Field(description="ID существующей записи")
    action: str = Field(description="reschedule | update_service | update_master")
    new_start_at: Optional[datetime] = None
    new_service_id: Optional[str] = None
    new_master_id: Optional[str] = None
    reason: Optional[str] = Field(None, description="Причина изменения")


class UpdateBookingResult(BaseModel):
    booking_id: str
    status: str
    summary: str = Field(description="Обновлённое описание записи")
    changes: dict = Field(description="Что изменилось")


async def update_booking(
    tenant_id: UUID,
    params: UpdateBookingParams,
    booking_service: BookingServiceInterface,
) -> UpdateBookingResult:
    """
    Обновляет существующую запись (перенос, смена услуги/мастера).
    Проверяет конфликты слотов при переносе.
    """
    result = await booking_service.update_booking(tenant_id, UUID(params.booking_id), data=params.model_dump())
    return UpdateBookingResult(**result)


TOOL_REGISTRY["update_booking"] = ToolDef(
    name="update_booking",
    description="Перенести или изменить существующую запись.",
    params_schema=UpdateBookingParams.model_json_schema(),
    returns_schema=UpdateBookingResult.model_json_schema(),
)


# ===== Tool 7: cancel_booking =====

class CancelBookingParams(BaseModel):
    booking_id: str = Field(description="ID записи для отмены")
    reason: str = Field(description="Причина: client_request | no_show | other")
    comment: Optional[str] = None


class CancelBookingResult(BaseModel):
    booking_id: str
    status: str = "cancelled"
    cancelled_at: datetime
    penalty_info: Optional[str] = Field(None, description="Информация о штрафе, если применимо")


async def cancel_booking(
    tenant_id: UUID,
    params: CancelBookingParams,
    booking_service: BookingServiceInterface,
) -> CancelBookingResult:
    """
    Отменяет запись.
    """
    result = await booking_service.cancel_booking(
        tenant_id,
        UUID(params.booking_id),
        reason=params.reason,
        comment=params.comment,
    )
    return CancelBookingResult(**result)


TOOL_REGISTRY["cancel_booking"] = ToolDef(
    name="cancel_booking",
    description="Отменить запись клиента.",
    params_schema=CancelBookingParams.model_json_schema(),
    returns_schema=CancelBookingResult.model_json_schema(),
)
