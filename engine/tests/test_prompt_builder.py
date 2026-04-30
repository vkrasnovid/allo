"""Tests for the prompt builder."""

from src.prompts.builder import (
    build_system_prompt,
    build_tool_definitions,
    PromptBlock,
    ClientContext,
)


def test_build_system_prompt_basic():
    """Basic prompt has business name."""
    prompt = build_system_prompt(business_name="Тестовый салон")
    assert "Тестовый салон" in prompt
    assert "голосовой AI-секретарь" in prompt
    assert "ПО-РУССКИ" in prompt
    assert "Просто спросить" in prompt


def test_build_system_prompt_with_blocks():
    """Blocks are included at proper positions."""
    blocks = [
        PromptBlock("greeting", "Привет!", position=1),
        PromptBlock("farewell", "Пока!", position=2),
    ]
    prompt = build_system_prompt(
        business_name="Салон",
        blocks=blocks,
    )
    assert "GREETING" in prompt
    assert "Привет!" in prompt
    assert "FAREWELL" in prompt
    assert "Пока!" in prompt


def test_build_system_prompt_with_client_context():
    """Client context is injected."""
    ctx = ClientContext(
        name="Мария",
        total_visits=3,
        preferred_master_name="Анна",
        preferred_services=["стрижка", "окрашивание"],
    )
    prompt = build_system_prompt(
        business_name="Салон",
        client_context=ctx,
    )
    assert "Мария" in prompt
    assert "3" in prompt
    assert "Анна" in prompt
    assert "стрижка" in prompt


def test_build_tool_definitions():
    """All 9 tools are defined."""
    tools = build_tool_definitions()
    tool_names = [t["function"]["name"] for t in tools]
    assert len(tools) == 9
    assert "get_services" in tool_names
    assert "get_masters" in tool_names
    assert "find_slots" in tool_names
    assert "create_booking" in tool_names
    assert "find_booking" in tool_names
    assert "update_booking" in tool_names
    assert "cancel_booking" in tool_names
    assert "get_business_info" in tool_names
    assert "escalate_to_human" in tool_names


def test_create_booking_has_required_params():
    """create_booking tool has required params."""
    tools = build_tool_definitions()
    create_tool = [t for t in tools if t["function"]["name"] == "create_booking"][0]
    params = create_tool["function"]["parameters"]
    assert "client_phone" in params["required"]
    assert "client_name" in params["required"]
    assert "master_id" in params["required"]
    assert "service_id" in params["required"]
    assert "start_at" in params["required"]
