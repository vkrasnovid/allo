"""
Tool Registry & Router.
Registers tool schemas from shared library, routes tool calls to Booking Service REST API.
"""

from typing import Any
from uuid import UUID

import httpx

from shared.tools.protocols import TOOL_REGISTRY


class ToolRouter:
    """Routes tool calls from the AI engine to the booking service."""

    def __init__(self, booking_api_url: str):
        self.booking_api_url = booking_api_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)

    def get_tool_definitions(self) -> list[dict]:
        """Return all tool definitions formatted for LLM consumption (OpenAI-like format)."""
        tools = []
        for name, tool_def in TOOL_REGISTRY.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "parameters": tool_def.params_schema,
                },
            })
        return tools

    async def execute_tool(self, tool_name: str, args: dict, tenant_id: str) -> dict:
        """Execute a tool call by routing to the booking service."""
        if tool_name not in TOOL_REGISTRY:
            raise ValueError(f"Unknown tool: {tool_name}")

        endpoint_map = {
            "get_services": "GET /services",
            "get_masters": "GET /masters",
            "find_slots": "GET /slots",
            "create_booking": "POST /bookings",
            "find_booking": "GET /bookings",
            "update_booking": "PATCH /bookings/{booking_id}",
            "cancel_booking": "DELETE /bookings/{booking_id}",
            "get_business_info": "GET /info",
            "escalate_to_human": "POST /escalate",
        }

        endpoint = endpoint_map.get(tool_name)
        if not endpoint:
            raise ValueError(f"No endpoint mapping for tool: {tool_name}")

        method, path_template = endpoint.split(" ", 1)
        path = path_template
        booking_id = args.pop("booking_id", None)
        if "{booking_id}" in path:
            path = path.replace("{booking_id}", str(booking_id))

        url = f"{self.booking_api_url}/tenants/{tenant_id}{path}"

        if method == "POST":
            resp = await self.client.post(url, json=args)
        elif method == "PATCH":
            resp = await self.client.patch(url, params=args)
        elif method == "DELETE":
            resp = await self.client.delete(url, params=args)
        else:
            resp = await self.client.get(url, params=args)

        resp.raise_for_status()
        return self._normalize_tool_result(tool_name, resp.json())

    def _normalize_tool_result(self, tool_name: str, result: Any) -> dict:
        """Normalize API responses into the expected tool format."""
        if tool_name == "create_booking":
            return {
                "booking_id": result["booking_id"],
                "status": result["status"],
                "yclients_id": result.get("yclients_id"),
                "summary": result["summary"],
            }
        elif tool_name == "find_booking":
            return {"bookings": result.get("bookings", [])}
        elif tool_name in ("update_booking",):
            return {
                "booking_id": result["booking_id"],
                "status": result["status"],
                "summary": result["summary"],
                "changes": result.get("changes", {}),
            }
        elif tool_name == "get_business_info":
            return {"business": result}
        return result

    async def close(self):
        await self.client.aclose()
