"""Unit tests for the shared tools library."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal

from shared.tools import (
    get_services, GetServicesParams,
    get_masters, GetMastersParams,
    find_slots, FindSlotsParams,
    create_booking, CreateBookingParams,
    find_booking, FindBookingParams,
    update_booking, UpdateBookingParams,
    cancel_booking, CancelBookingParams,
    get_business_info, GetBusinessInfoParams,
    escalate_to_human, EscalateParams,
)


class MockBookingService:
    """Mock booking service for testing tools."""

    def __init__(self):
        self.tenant_id = uuid4()

    async def get_services(self, tenant_id, category=None):
        return [
            {"id": str(uuid4()), "name": "Стрижка женская", "duration_min": 60, "price_rub": 2500.0,
             "category": "стрижки", "description": "Классическая стрижка"},
            {"id": str(uuid4()), "name": "Маникюр", "duration_min": 60, "price_rub": 2000.0,
             "category": "маникюр", "description": "Классический маникюр"},
        ]

    async def get_masters(self, tenant_id, service_id=None):
        return [
            {"id": str(uuid4()), "name": "Анна Петрова", "specialization": "Стрижки, окрашивание", "rating": 4.8},
            {"id": str(uuid4()), "name": "Елена Соколова", "specialization": "Маникюр, педикюр", "rating": 4.9},
        ]

    async def find_slots(self, tenant_id, date, master_id=None, service_id=None):
        return [
            {"start": datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc),
             "end": datetime(2026, 5, 1, 15, 0, tzinfo=timezone.utc),
             "master_id": str(uuid4()), "master_name": "Анна Петрова"},
        ]

    async def create_booking(self, tenant_id, data: dict):
        return {
            "booking_id": str(uuid4()),
            "status": "confirmed",
            "summary": "Стрижка у Анны, 01.05.2026 в 14:00, 2500 ₽",
        }

    async def find_bookings(self, tenant_id, client_phone, status=None, limit=5):
        return [
            {"booking_id": str(uuid4()), "service_name": "Стрижка женская",
             "master_name": "Анна Петрова", "start_at": datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc),
             "status": "confirmed", "price_rub": 2500.0},
        ]

    async def update_booking(self, tenant_id, booking_id, data: dict):
        return {
            "booking_id": str(booking_id),
            "status": "confirmed",
            "summary": "Запись обновлена",
            "changes": {"old_start": "2026-04-15T14:00:00", "new_start": "2026-05-01T10:00:00"},
        }

    async def cancel_booking(self, tenant_id, booking_id, reason, comment=None):
        return {
            "booking_id": str(booking_id),
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc),
        }

    async def get_business_info(self, tenant_id):
        return {
            "name": "Салон красоты Элегант",
            "address": "ул. Тверская, д. 15",
            "phone": "+74951234567",
            "work_hours": {"mon-fri": "09:00-21:00", "sat": "10:00-20:00", "sun": "10:00-18:00"},
        }

    async def escalate(self, tenant_id, data: dict):
        return {
            "action": "transfer",
            "forward_to": "+79991234567",
            "transfer_initiated": True,
        }

    async def get_or_create_client(self, tenant_id, phone, name=None):
        return {"client": {"id": str(uuid4()), "name": name or "Клиент", "phone": phone}}


@pytest.fixture
def mock_service():
    return MockBookingService()


@pytest.mark.asyncio
async def test_get_services(mock_service):
    params = GetServicesParams(category="стрижки")
    result = await get_services(mock_service.tenant_id, params, mock_service)
    assert len(result.services) == 2
    assert result.services[0].name == "Стрижка женская"
    assert result.services[0].price_rub == 2500.0


@pytest.mark.asyncio
async def test_get_services_no_filter(mock_service):
    params = GetServicesParams()
    result = await get_services(mock_service.tenant_id, params, mock_service)
    assert len(result.services) == 2


@pytest.mark.asyncio
async def test_get_masters(mock_service):
    params = GetMastersParams()
    result = await get_masters(mock_service.tenant_id, params, mock_service)
    assert len(result.masters) == 2
    assert result.masters[0].name == "Анна Петрова"


@pytest.mark.asyncio
async def test_find_slots(mock_service):
    params = FindSlotsParams(date="2026-05-01")
    result = await find_slots(mock_service.tenant_id, params, mock_service)
    assert len(result.slots) == 1
    assert result.slots[0].master_name == "Анна Петрова"


@pytest.mark.asyncio
async def test_create_booking(mock_service):
    params = CreateBookingParams(
        client_phone="+79161234567",
        client_name="Мария",
        master_id=str(uuid4()),
        service_id=str(uuid4()),
        start_at=datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc),
    )
    result = await create_booking(mock_service.tenant_id, params, mock_service)
    assert result.status == "confirmed"
    assert "Стрижка" in result.summary


@pytest.mark.asyncio
async def test_find_booking(mock_service):
    params = FindBookingParams(client_phone="+79161234567")
    result = await find_booking(mock_service.tenant_id, params, mock_service)
    assert len(result.bookings) == 1
    assert result.bookings[0].service_name == "Стрижка женская"


@pytest.mark.asyncio
async def test_update_booking(mock_service):
    booking_id = uuid4()
    params = UpdateBookingParams(
        booking_id=str(booking_id),
        action="reschedule",
        new_start_at=datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
    )
    result = await update_booking(mock_service.tenant_id, params, mock_service)
    assert result.status == "confirmed"
    assert "changes" in result.model_dump()


@pytest.mark.asyncio
async def test_cancel_booking(mock_service):
    booking_id = uuid4()
    params = CancelBookingParams(booking_id=str(booking_id), reason="client_request")
    result = await cancel_booking(mock_service.tenant_id, params, mock_service)
    assert result.status == "cancelled"


@pytest.mark.asyncio
async def test_get_business_info(mock_service):
    params = GetBusinessInfoParams()
    result = await get_business_info(mock_service.tenant_id, params, mock_service)
    assert result.business.name == "Салон красоты Элегант"
    assert result.business.phone == "+74951234567"


@pytest.mark.asyncio
async def test_escalate_to_human(mock_service):
    params = EscalateParams(call_id=str(uuid4()), reason="complaint")
    result = await escalate_to_human(mock_service.tenant_id, params, mock_service)
    assert result.action == "transfer"
    assert "+79991234567" in result.forward_to
