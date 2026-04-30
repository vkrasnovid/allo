"""Tests for prompt manager."""
import pytest
from uuid import UUID

from engine.src.prompts import PromptManager, BASE_SYSTEM_PROMPT
from shared.models.prompts import PromptProfile, PromptBlock


@pytest.fixture
def prompt_manager():
    return PromptManager(booking_api_url="http://localhost:8003")


@pytest.fixture
def test_profile():
    return PromptProfile(
        id=UUID(int=1),
        tenant_id=UUID(int=1),
        name="beauty_salon",
        is_active=True,
        blocks=[
            PromptBlock(
                id=UUID(int=2),
                profile_id=UUID(int=1),
                block_key="greeting",
                content="Салон красоты «Элегант», здравствуйте! Чем могу помочь?",
                position=1,
                is_active=True,
            ),
            PromptBlock(
                id=UUID(int=3),
                profile_id=UUID(int=1),
                block_key="tone",
                content="Ты общаешься дружелюбно, но без панибратства. Обращайся на «Вы».",
                position=2,
                is_active=True,
            ),
            PromptBlock(
                id=UUID(int=4),
                profile_id=UUID(int=1),
                block_key="rules",
                content="Правила: отмена за 2 часа, опоздание более 15 минут — перенос.",
                position=3,
                is_active=True,
            ),
            PromptBlock(
                id=UUID(int=5),
                profile_id=UUID(int=1),
                block_key="farewell",
                content="Будем ждать вас в салоне! Всего доброго!",
                position=4,
                is_active=True,
            ),
        ],
    )


def test_compose_prompt_includes_base(prompt_manager, test_profile):
    composed = prompt_manager.compose_prompt(
        profile=test_profile,
        business_name="Салон красоты Элегант",
    )
    assert "Салон красоты Элегант" in composed.system_prompt
    assert "голосовой AI-секретарь" in composed.system_prompt


def test_compose_prompt_includes_blocks(prompt_manager, test_profile):
    composed = prompt_manager.compose_prompt(profile=test_profile)
    assert "GREETING" in composed.system_prompt
    assert "Салон красоты «Элегант»" in composed.system_prompt
    assert "TONE" in composed.system_prompt
    assert "RULES" in composed.system_prompt
    assert "FAREWELL" in composed.system_prompt


def test_compose_prompt_blocks_used(prompt_manager, test_profile):
    composed = prompt_manager.compose_prompt(profile=test_profile)
    assert "greeting" in composed.blocks_used
    assert "tone" in composed.blocks_used
    assert "farewell" in composed.blocks_used


def test_compose_prompt_ordering(prompt_manager, test_profile):
    composed = prompt_manager.compose_prompt(profile=test_profile)
    # Blocks should appear in order of position
    greeting_pos = composed.system_prompt.find("GREETING")
    tone_pos = composed.system_prompt.find("TONE")
    rules_pos = composed.system_prompt.find("RULES")
    farewell_pos = composed.system_prompt.find("FAREWELL")
    assert greeting_pos < tone_pos < rules_pos < farewell_pos


def test_compose_prompt_with_client_context(prompt_manager, test_profile):
    client_context = {
        "name": "Мария Иванова",
        "total_visits": 5,
        "last_visit_at": "2026-03-15",
        "preferred_master": "Анна",
        "preferred_services": ["стрижка", "окрашивание"],
    }
    composed = prompt_manager.compose_prompt(
        profile=test_profile,
        client_context=client_context,
    )
    assert "Мария Иванова" in composed.system_prompt
    assert "total_visits" in composed.system_prompt or "5" in composed.system_prompt
    assert "Анна" in composed.system_prompt
    assert "стрижка" in composed.system_prompt


def test_compose_prompt_inactive_block_skipped(prompt_manager):
    """Inactive blocks should not appear in the composed prompt."""
    profile = PromptProfile(
        id=UUID(int=1),
        tenant_id=UUID(int=1),
        name="test",
        blocks=[
            PromptBlock(
                id=UUID(int=2),
                profile_id=UUID(int=1),
                block_key="greeting",
                content="Hello",
                position=1,
                is_active=False,  # inactive
            ),
        ],
    )
    composed = prompt_manager.compose_prompt(profile=profile)
    assert "GREETING" not in composed.system_prompt
    assert "greeting" not in composed.blocks_used


def test_base_prompt_has_rules(prompt_manager):
    assert "НИКОГДА не выдумываешь данные" in BASE_SYSTEM_PROMPT
    assert "Просто спросить" in BASE_SYSTEM_PROMPT
    assert "эскалации" in BASE_SYSTEM_PROMPT
    assert "30-60 секунд" in BASE_SYSTEM_PROMPT
    assert "ПО-РУССКИ" in BASE_SYSTEM_PROMPT


def test_default_profile(prompt_manager):
    profile = prompt_manager._get_default_profile("00000000-0000-0000-0000-000000000001")
    assert profile.name == "beauty_salon_default"
    assert profile.is_active
    assert len(profile.blocks) == 3
