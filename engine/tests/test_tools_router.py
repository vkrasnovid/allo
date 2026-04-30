"""Tests for tool router."""
import pytest

from engine.src.tools import ToolRouter


@pytest.fixture
def router():
    return ToolRouter(booking_api_url="http://localhost:8003")


def test_tool_registry_has_all_tools(router):
    tools = router.get_tool_definitions()
    assert len(tools) == 9

    tool_names = {t["function"]["name"] for t in tools}
    expected = {
        "get_services", "get_masters", "find_slots",
        "create_booking", "find_booking", "update_booking",
        "cancel_booking", "get_business_info", "escalate_to_human",
    }
    assert tool_names == expected


def test_tool_definitions_have_descriptions(router):
    tools = router.get_tool_definitions()
    for t in tools:
        assert len(t["function"]["description"]) > 10
        assert "parameters" in t["function"]
        assert "type" in t["function"]["parameters"]


def test_tool_definitions_openai_format(router):
    """Tool definitions should match OpenAI function calling format."""
    tools = router.get_tool_definitions()
    for t in tools:
        assert t["type"] == "function"
        assert "name" in t["function"]
        assert "description" in t["function"]


def test_tool_schemas_have_properties(router):
    tools = router.get_tool_definitions()
    for t in tools:
        # All tools should have parameters dict even if empty
        assert "parameters" in t["function"]
        assert "properties" in t["function"]["parameters"]
        # get_business_info legitimately has 0 params
