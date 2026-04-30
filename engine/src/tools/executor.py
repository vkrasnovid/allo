"""Tool executor — runs tools from the shared library or via HTTP to booking service."""

import json
import logging
from typing import Any

import httpx

from src.dialog.guard import validate_tool_call_params, hallucination_log

logger = logging.getLogger(__name__)


class BookingServiceClient:
    """
    HTTP client for booking service.
    Injected into tools as BookingServiceInterface.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def get_services(self, tenant_id, category: str = None) -> list[dict]:
        params = {}
        if category:
            params["category"] = category
        resp = await self.client.get(
            f"{self.base_url}/tenants/{tenant_id}/services",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("services", [])

    async def get_masters(self, tenant_id, service_id=None) -> list[dict]:
        params = {}
        if service_id:
            params["service_id"] = str(service_id)
        resp = await self.client.get(
            f"{self.base_url}/tenants/{tenant_id}/masters",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("masters", [])

    async def find_slots(self, tenant_id, date, master_id=None, service_id=None) -> list[dict]:
        params = {"date": date.isoformat() if hasattr(date, 'isoformat') else date}
        if master_id:
            params["master_id"] = str(master_id)
        if service_id:
            params["service_id"] = str(service_id)
        resp = await self.client.get(
            f"{self.base_url}/tenants/{tenant_id}/slots",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("slots", [])

    async def create_booking(self, tenant_id, data: dict) -> dict:
        resp = await self.client.post(
            f"{self.base_url}/tenants/{tenant_id}/bookings",
            json=data,
        )
        resp.raise_for_status()
        return resp.json()

    async def find_bookings(self, tenant_id, client_phone: str, status=None, limit=5) -> list[dict]:
        params = {"client_phone": client_phone, "limit": limit}
        if status:
            params["status"] = status
        resp = await self.client.get(
            f"{self.base_url}/tenants/{tenant_id}/bookings",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("bookings", [])

    async def update_booking(self, tenant_id, booking_id, data: dict) -> dict:
        resp = await self.client.patch(
            f"{self.base_url}/tenants/{tenant_id}/bookings/{booking_id}",
            json=data,
        )
        resp.raise_for_status()
        return resp.json()

    async def cancel_booking(self, tenant_id, booking_id, reason: str, comment=None) -> dict:
        params = {"reason": reason}
        if comment:
            params["comment"] = comment
        resp = await self.client.delete(
            f"{self.base_url}/tenants/{tenant_id}/bookings/{booking_id}",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_business_info(self, tenant_id) -> dict:
        resp = await self.client.get(
            f"{self.base_url}/tenants/{tenant_id}/info",
        )
        resp.raise_for_status()
        return resp.json()

    async def escalate(self, tenant_id, data: dict) -> dict:
        resp = await self.client.post(
            f"{self.base_url}/tenants/{tenant_id}/escalate",
            json=data,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_or_create_client(self, tenant_id, phone: str, name=None) -> dict:
        resp = await self.client.get(
            f"{self.base_url}/tenants/{tenant_id}/clients/by-phone/{phone}",
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": "CLIENT_NOT_FOUND"}


class ToolExecutor:
    """
    Executes tool calls from LLM against the booking service.
    """

    def __init__(self, booking_api_url: str):
        self.booking_client = BookingServiceClient(booking_api_url)

    async def close(self):
        await self.booking_client.close()

    async def execute_tool(
        self,
        tool_name: str,
        args: dict,
        tenant_id,
        call_id: str = None,
    ) -> dict:
        """
        Execute a tool and return the result.
        Validates params before sending and catches errors gracefully.
        """
        try:
            # Validate params against hallucinations
            validated_args = validate_tool_call_params(tool_name, args)
        except (ValueError, KeyError) as e:
            hallucination_log.log(tool_name, args, str(e))
            return {
                "error": f"INVALID_PARAMS: {str(e)}",
                "tool": tool_name,
            }

        try:
            result = await self._route_tool(tool_name, validated_args, tenant_id)
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"Tool {tool_name} HTTP error: {e}")
            try:
                detail = e.response.json()
            except (json.JSONDecodeError, AttributeError):
                detail = {"error": "UNKNOWN", "message": str(e)}
            return {
                "error": detail.get("error", "HTTP_ERROR"),
                "message": detail.get("message", str(e)),
                "tool": tool_name,
            }
        except httpx.RequestError as e:
            logger.error(f"Tool {tool_name} request error: {e}")
            return {
                "error": "SERVICE_UNAVAILABLE",
                "message": "Сервис временно недоступен",
                "tool": tool_name,
            }
        except Exception as e:
            logger.error(f"Tool {tool_name} unexpected error: {e}")
            return {
                "error": "INTERNAL_ERROR",
                "message": str(e),
                "tool": tool_name,
            }

    async def _route_tool(
        self,
        tool_name: str,
        args: dict,
        tenant_id,
    ) -> dict:
        """Route tool call to the appropriate handler."""
        bc = self.booking_client

        if tool_name == "get_services":
            services = await bc.get_services(tenant_id, category=args.get("category"))
            return {"services": services}

        elif tool_name == "get_masters":
            masters = await bc.get_masters(tenant_id, service_id=args.get("service_id"))
            return {"masters": masters}

        elif tool_name == "find_slots":
            from datetime import date
            date_val = date.fromisoformat(args["date"]) if isinstance(args.get("date"), str) else args.get("date")
            slots = await bc.find_slots(
                tenant_id,
                date=date_val,
                master_id=args.get("master_id"),
                service_id=args.get("service_id"),
            )
            return {"slots": slots}

        elif tool_name == "create_booking":
            result = await bc.create_booking(tenant_id, args)
            return result

        elif tool_name == "find_booking":
            bookings = await bc.find_bookings(
                tenant_id,
                client_phone=args["client_phone"],
                status=args.get("status"),
                limit=args.get("limit", 5),
            )
            return {"bookings": bookings}

        elif tool_name == "update_booking":
            booking_id = args.pop("booking_id")
            result = await bc.update_booking(tenant_id, booking_id, args)
            return result

        elif tool_name == "cancel_booking":
            booking_id = args.pop("booking_id")
            result = await bc.cancel_booking(
                tenant_id, booking_id,
                reason=args.get("reason", "client_request"),
                comment=args.get("comment"),
            )
            return result

        elif tool_name == "get_business_info":
            info = await bc.get_business_info(tenant_id)
            return {"business": info}

        elif tool_name == "escalate_to_human":
            result = await bc.escalate(tenant_id, args)
            return result

        else:
            return {"error": f"UNKNOWN_TOOL: {tool_name}"}
