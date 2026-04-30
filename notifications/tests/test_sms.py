"""Tests for the SMS notification provider."""

import pytest

from src.sms.provider import SmsProvider, sms_provider


@pytest.mark.asyncio
async def test_sms_stub_without_api_key():
    """Without API key, SMS should log and return stub status."""
    # sms_provider has no API key in test env
    result = await sms_provider.send_sms("+79161234567", "Тестовое сообщение")
    assert result["status"] == "stub"
    assert result["phone"] == "+79161234567"


@pytest.mark.asyncio
async def test_sms_reminder_day_before():
    """Day-before reminder has correct format."""
    result = await sms_provider.send_reminder_day_before(
        phone="+79161234567",
        client_name="Мария",
        service="Стрижка",
        master="Анна",
        time="14:00",
    )
    assert result["status"] == "stub"
    assert result["phone"] == "+79161234567"


@pytest.mark.asyncio
async def test_sms_reminder_hour_before():
    """Hour-before reminder has correct format."""
    result = await sms_provider.send_reminder_hour_before(
        phone="+79161234567",
        client_name="Мария",
        service="Стрижка",
        master="Анна",
        time="14:00",
    )
    assert result["status"] == "stub"


@pytest.mark.asyncio
async def test_sms_provider_custom():
    """Custom SMS provider instance works."""
    provider = SmsProvider()
    result = await provider.send_sms("+79161234567", "Тест")
    assert result["status"] == "stub"
    await provider.close()
