"""Conversational Engine — FastAPI application."""

import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.state.redis_manager import DialogStateManager
from src.tools.executor import ToolExecutor
from src.dialog.manager import DialogManager
from src.dialog.guard import hallucination_log

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

BOOKING_API_URL = os.getenv("BOOKING_API_URL", "http://booking:8003/api/v1")

# Global state
state_manager = DialogStateManager()
tool_executor = ToolExecutor(BOOKING_API_URL)
dialog_manager = DialogManager(
    state_manager=state_manager,
    tool_executor=tool_executor,
    llm_client=None,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await state_manager.init()
    logger.info("Engine started")
    yield
    await state_manager.close()
    await tool_executor.close()
    logger.info("Engine stopped")


app = FastAPI(
    title="Алло — Conversational Engine",
    description="Dialog management & tool execution for voice AI secretary",
    version="0.1.0",
    lifespan=lifespan,
)


# ===== Request/Response Schemas =====

class MessageRequest(BaseModel):
    tenant_id: str
    call_id: str
    text: str
    client_phone: str | None = None


class ToolExecuteRequest(BaseModel):
    tenant_id: str
    call_id: str | None = None
    tool_name: str
    args: dict = {}


class DialogStateRequest(BaseModel):
    tenant_id: str
    call_id: str
    state: str | None = None


# ===== API Routes =====

@app.post("/api/engine/message")
async def process_message(body: MessageRequest):
    """Process a user message through the dialog."""
    result = await dialog_manager.process_user_message(
        tenant_id=body.tenant_id,
        call_id=body.call_id,
        text=body.text,
        client_phone=body.client_phone,
    )
    return result


@app.post("/api/engine/tool")
async def execute_tool(body: ToolExecuteRequest):
    """Execute a single tool and return the result."""
    result = await tool_executor.execute_tool(
        tool_name=body.tool_name,
        args=body.args,
        tenant_id=body.tenant_id,
        call_id=body.call_id,
    )
    return result


@app.post("/api/engine/state")
async def get_dialog_state(body: DialogStateRequest):
    """Get or update dialog state."""
    if body.state:
        await state_manager.set_state(body.tenant_id, body.call_id, body.state)
        return {"status": "updated", "state": body.state}

    current_state = await state_manager.get_state(body.tenant_id, body.call_id)
    return {
        "tenant_id": body.tenant_id,
        "call_id": body.call_id,
        "state": current_state,
        "context": await state_manager.get_all_context(body.tenant_id, body.call_id),
    }


@app.post("/api/engine/context")
async def set_context(body: dict):
    """Set dialog context values."""
    tenant_id = body.get("tenant_id")
    call_id = body.get("call_id")
    values = body.get("values", {})

    if not tenant_id or not call_id:
        raise HTTPException(status_code=422, detail="tenant_id and call_id required")

    for key, value in values.items():
        await state_manager.set_context(tenant_id, call_id, key, value)

    return {"status": "context_updated", "keys": list(values.keys())}


@app.post("/api/engine/clear")
async def clear_dialog(body: dict):
    """Clear dialog state for a call."""
    tenant_id = body.get("tenant_id")
    call_id = body.get("call_id")
    if tenant_id and call_id:
        await state_manager.clear_call(tenant_id, call_id)
    return {"status": "cleared"}


@app.get("/api/engine/stats")
async def get_stats():
    """Get engine statistics."""
    return {
        "hallucination_events": hallucination_log.get_stats(),
        "service": "engine",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "engine"}


@app.post("/api/engine/prompt")
async def build_prompt(body: dict):
    """Build a system prompt for testing."""
    from src.prompts.builder import build_system_prompt, build_tool_definitions
    prompt = build_system_prompt(
        business_name=body.get("business_name", "Тестовый салон"),
    )
    return {
        "prompt": prompt,
        "tool_definitions": build_tool_definitions(),
    }
