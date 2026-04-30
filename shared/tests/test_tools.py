"""Tests for the shared tools library."""
import pytest
from uuid import UUID

from shared.tools.services import get_services, GetServicesParams
from shared.tools.masters import get_masters, GetMastersParams
from shared.tools.calendar import find_slots, FindSlotsParams
from shared.tools.booking import (
    create_booking,
    CreateBookingParams,
    find_booking,
    FindBookingParams,
    update_booking,
    UpdateBookingParams,
    cancel_booking,
    CancelBookingParams,
)
from shared.tools.business import get_business_info, GetBusinessInfoParams
from shared.tools.escalation import escalate_to_human, EscalateParams
from shared.tools.protocols import TOOL_REGISTRY


class MockBookingService:
    """Mock booking service for testing tools."""

    async def get_services(self, tenant_id: UUID, category=None):
        return [
            {"id": str(UUID(int=1)), "name": "Стрижка", "duration_min": 60, "price_rub": 2500.0, "category": "стрижки"},
            {"id": str(UUID(int=2)), "name": "Маникюр", "duration_min": 60, "price_rub": 2000.0, "category": "маникюр"},
        ]

    async def get_masters(self, tenant_id: UUID, service_id=None):
        return [
            {"id": str(UUID(int=10)), "name": "Анна", "specialization": "Стрижки"},
            {"id": str(UUID(int=11)), "name": "Елена", "specialization": "Маникюр"},
        ]

    async def find_slots(self, tenant_id: UUID, date=None, master_id=None, service_id=None):
        from datetime import datetime
        return [
            {"start": datetime(2026, 5, 1, 10, 0), "end": datetime(2026, 5, 1, 11, 0),
             "master_id": str(UUID(int=10)), "master_name": "Анна"},
        ]

    async def create_booking(self, tenant_id: UUID, data: dict):
        return {
            "booking_id": str(UUID(int=100)),
            "status": "confirmed",
            "yclients_id": None,
            "summary": "Стрижка у Анны, 01.05 в 10:00, 2500.0 ₽",
        }

    async def find_bookings(self, tenant_id: UUID, client_phone: str, status=None, limit=5):
        from datetime import datetime
        return [
            {"booking_id": str(UUID(int=100)), "service_name": "Стрижка",
             "master_name": "Анна", "start_at": datetime(2026, 5, 1, 10, 0),
             "status": "confirmed", "price_rub": 2500.0},
        ]

    async def update_booking(self, tenant_id: UUID, booking_id: UUID, data: dict):
        return {
            "booking_id": str(booking_id),
            "status": "confirmed",
            "summary": "Updated booking",
            "changes": {"start_at": {"from": "2026-04-01", "to": "2026-05-01"}},
        }

    async def cancel_booking(self, tenant_id: UUID, booking_id: UUID, reason: str, comment=None):
        from datetime import datetime
        return {
            "booking_id": str(booking_id),
            "status": "cancelled",
            "cancelled_at": datetime(2026, 4, 29, 21, 0).isoformat(),
        }

    async def get_business_info(self, tenant_id: UUID):
        return {
            "name": "Тестовый салон",
            "address": "ул. Тестовая, 1",
            "phone": "+74951234567",
            "work_hours": {"mon_fri": "09:00-21:00", "sat": "10:00-20:00", "sun": "10:00-18:00"},
            "description": "Тестовый салон для разработки",
        }

    async def escalate(self, tenant_id: UUID, data: dict):
        return {
            "action": "transfer",
            "forward_to": "+79991234567",
            "transfer_initiated": True,
        }

    async def get_or_create_client(self, tenant_id: UUID, phone: str, name=None):
        return {"id": str(UUID(int=50)), "name": name, "phone": phone, "total_visits": 0, "created": True}


TEST_TENANT = UUID("00000000-0000-0000-0000-000000000001")
mock_svc = MockBookingService()


@pytest.mark.asyncio
async def test_get_services():
    params = GetServicesParams(category=None)
    result = await get_services(TEST_TENANT, params, mock_svc)
    assert len(result.services) == 2
    assert result.services[0].name == "Стрижка"


@pytest.mark.asyncio
async def test_get_masters():
    params = GetMastersParams(service_id=None)
    result = await get_masters(TEST_TENANT, params, mock_svc)
    assert len(result.masters) == 2
    assert result.masters[0].name == "Анна"


@pytest.mark.asyncio
async def test_find_slots():
    from datetime import date
    params = FindSlotsParams(date=date(2026, 5, 1))
    result = await find_slots(TEST_TENANT, params, mock_svc)
    assert len(result.slots) >= 1


@pytest.mark.asyncio
async def test_create_booking():
    from datetime import datetime
    params = CreateBookingParams(
        client_phone="+79161234567",
        client_name="Мария",
        master_id=str(UUID(int=10)),
        service_id=str(UUID(int=1)),
        start_at=datetime(2026, 5, 1, 10, 0),
    )
    result = await create_booking(TEST_TENANT, params, mock_svc)
    assert result.status == "confirmed"
    assert "Стрижка" in result.summary


@pytest.mark.asyncio
async def test_find_booking():
    params = FindBookingParams(client_phone="+79161234567")
    result = await find_booking(TEST_TENANT, params, mock_svc)
    assert len(result.bookings) == 1


@pytest.mark.asyncio
async def test_update_booking():
    params = UpdateBookingParams(
        booking_id=str(UUID(int=100)),
        action="reschedule",
        reason="client_request",
    )
    result = await update_booking(TEST_TENANT, params, mock_svc)
    assert result.status == "confirmed"
    assert "changes" in result.model_dump()


@pytest.mark.asyncio
async def test_cancel_booking():
    params = CancelBookingParams(
        booking_id=str(UUID(int=100)),
        reason="client_request",
    )
    result = await cancel_booking(TEST_TENANT, params, mock_svc)
    assert result.status == "cancelled"


@pytest.mark.asyncio
async def test_get_business_info():
    params = GetBusinessInfoParams()
    result = await get_business_info(TEST_TENANT, params, mock_svc)
    assert result.business.name == "Тестовый салон"
    assert "mon_fri" in result.business.work_hours


@pytest.mark.asyncio
async def test_escalate():
    params = EscalateParams(
        call_id="test-call-1",
        reason="complaint",
        client_summary="Клиент недоволен ценой",
    )
    result = await escalate_to_human(TEST_TENANT, params, mock_svc)
    assert result.action == "transfer"
    assert result.transfer_initiated


@pytest.mark.asyncio
async def test_tool_registry_size():
    assert len(TOOL_REGISTRY) == 9  # All 9 tools registered


@pytest.mark.asyncio
async def test_get_services_category_filter():
    params = GetServicesParams(category="маникюр")
    result = await get_services(TEST_TENANT, params, mock_svc)
    assert len(result.services) == 2  # Mock returns all regardless


@pytest.mark.asyncio
async def test_find_booking_limit():
    params = FindBookingParams(client_phone="+79161234567", limit=3)
    result = await find_booking(TEST_TENANT, params, mock_svc)
    assert len(result.bookings) <= 3
