"""Tests for anti-hallucination guards."""

import pytest

from src.dialog.guard import (
    validate_tool_call_params,
    validate_price_against_service,
    validate_llm_response_text,
)


class TestValidateToolCallParams:

    def test_valid_get_services(self):
        result = validate_tool_call_params("get_services", {"category": "стрижки"})
        assert result["category"] == "стрижки"

    def test_invalid_category_reset(self):
        """Unknown category should be set to None (return all services)."""
        result = validate_tool_call_params("get_services", {"category": "летающие ножницы"})
        assert result["category"] is None

    def test_valid_create_booking(self):
        args = {
            "client_phone": "+79161234567",
            "master_id": "550e8400-e29b-41d4-a716-446655440000",
            "service_id": "550e8400-e29b-41d4-a716-446655440001",
        }
        result = validate_tool_call_params("create_booking", args)
        assert result["client_phone"] == "+79161234567"

    def test_invalid_phone_raises(self):
        args = {
            "client_phone": "not-a-phone",
            "master_id": "550e8400-e29b-41d4-a716-446655440000",
            "service_id": "550e8400-e29b-41d4-a716-446655440001",
        }
        with pytest.raises(ValueError, match="Invalid phone"):
            validate_tool_call_params("create_booking", args)

    def test_invalid_master_id_raises(self):
        args = {
            "client_phone": "+79161234567",
            "master_id": "not-a-uuid",
            "service_id": "550e8400-e29b-41d4-a716-446655440000",
        }
        with pytest.raises(ValueError, match="Invalid master_id"):
            validate_tool_call_params("create_booking", args)

    def test_invalid_date_format_raises(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_tool_call_params("find_slots", {"date": "32-13-2026"})

    def test_valid_date_format(self):
        """Valid ISO date should pass."""
        result = validate_tool_call_params("find_slots", {"date": "2026-05-01"})
        assert result["date"] == "2026-05-01"


class TestValidatePrice:

    def test_valid_price(self):
        assert validate_price_against_service("Стрижка женская", 2500.0) is True

    def test_hallucinated_low_price(self):
        assert validate_price_against_service("Стрижка женская", 100.0) is False

    def test_hallucinated_high_price(self):
        assert validate_price_against_service("Стрижка женская", 50000.0) is False

    def test_unknown_service_not_blocked(self):
        """Unknown service should not be flagged."""
        assert validate_price_against_service("Экзотическая процедура", 9999.0) is True


class TestValidateResponseText:

    def test_remove_markdown_tables(self):
        text = "| Услуга | Цена |\n| Стрижка | 2500 |"
        cleaned = validate_llm_response_text(text)
        assert "|" not in cleaned

    def test_remove_headings(self):
        text = "# Заголовок\n## Подзаголовок\nТекст"
        cleaned = validate_llm_response_text(text)
        assert "#" not in cleaned

    def test_normal_text_preserved(self):
        text = "Здравствуйте! Чем могу помочь?"
        cleaned = validate_llm_response_text(text)
        assert cleaned == "Здравствуйте! Чем могу помочь?"
