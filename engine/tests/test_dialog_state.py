"""Tests for dialog state management (Redis)."""

import os
import pytest
from uuid import uuid4

os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from src.state.redis_manager import DialogStateManager


@pytest.fixture(autouse=True)
def _ensure_redis_url():
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.mark.asyncio
async def test_add_and_get_messages():
    sm = DialogStateManager()
    await sm.init()

    tenant_id = str(uuid4())
    call_id = str(uuid4())

    await sm.add_message(tenant_id, call_id, "user", "Здравствуйте")
    await sm.add_message(tenant_id, call_id, "assistant", "Чем могу помочь?")
    await sm.add_message(tenant_id, call_id, "user", "Хочу записаться на стрижку")

    messages = await sm.get_messages(tenant_id, call_id)
    assert len(messages) == 3
    assert messages[0]["content"] == "Здравствуйте"
    assert messages[-1]["content"] == "Хочу записаться на стрижку"

    llm_msgs = await sm.get_llm_messages(tenant_id, call_id)
    assert len(llm_msgs) == 3

    await sm.clear_call(tenant_id, call_id)
    await sm.close()


@pytest.mark.asyncio
async def test_context_management():
    sm = DialogStateManager()
    await sm.init()

    tenant_id = str(uuid4())
    call_id = str(uuid4())

    await sm.set_context(tenant_id, call_id, "business_name", "Салон красоты")
    await sm.set_context(tenant_id, call_id, "client_name", "Мария")

    context = await sm.get_all_context(tenant_id, call_id)
    assert context["business_name"] == "Салон красоты"
    assert context["client_name"] == "Мария"

    name = await sm.get_context(tenant_id, call_id, "business_name")
    assert name == "Салон красоты"

    await sm.clear_call(tenant_id, call_id)
    await sm.close()


@pytest.mark.asyncio
async def test_state_machine():
    sm = DialogStateManager()
    await sm.init()

    tenant_id = str(uuid4())
    call_id = str(uuid4())

    assert await sm.get_state(tenant_id, call_id) is None

    await sm.set_state(tenant_id, call_id, "greeting")
    assert await sm.get_state(tenant_id, call_id) == "greeting"

    await sm.set_state(tenant_id, call_id, "booking")
    assert await sm.get_state(tenant_id, call_id) == "booking"

    await sm.clear_call(tenant_id, call_id)
    assert await sm.get_state(tenant_id, call_id) is None

    await sm.close()


@pytest.mark.asyncio
async def test_client_booking_cache():
    sm = DialogStateManager()
    await sm.init()

    tenant_id = str(uuid4())
    phone = "+79161234567"

    bookings = [
        {"service_name": "Стрижка", "master_name": "Анна", "date": "2026-04-15"},
        {"service_name": "Маникюр", "master_name": "Елена", "date": "2026-04-01"},
    ]

    await sm.cache_client_bookings(tenant_id, phone, bookings)
    cached = await sm.get_history_for_client(tenant_id, phone)
    assert len(cached) == 2
    services = {b["service_name"] for b in cached}
    assert "Стрижка" in services
    assert "Маникюр" in services

    await sm.close()
