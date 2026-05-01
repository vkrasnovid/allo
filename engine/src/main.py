"""Conversational Engine — FastAPI application."""

import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.state.redis_manager import DialogStateManager
from src.tools.executor import ToolExecutor
from src.dialog.manager import DialogManager
from src.dialog.guard import hallucination_log
from src.llm import OpenClawLLMClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

BOOKING_API_URL = os.getenv("BOOKING_API_URL", "http://booking:8003/api/v1")

# Global state
state_manager = DialogStateManager()
tool_executor = ToolExecutor(BOOKING_API_URL)
# Initialize LLM client from env (graceful fallback)
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL", os.getenv("OPENCLAW_BASE_URL", "http://openclaw:4000"))
OPENCLAW_API_KEY = os.getenv("OPENCLAW_API_KEY", "")
llm_client = None
if OPENCLAW_API_KEY:
    try:
        llm_client = OpenClawLLMClient(
            base_url=OPENCLAW_API_URL,
            api_key=OPENCLAW_API_KEY,
        )
        logger.info("LLM client initialized")
    except Exception as e:
        logger.warning("Failed to initialize LLM client: %s", e)
else:
    logger.warning("OPENCLAW_API_KEY not set — LLM client disabled, stub responses will be used")

dialog_manager = DialogManager(
    state_manager=state_manager,
    tool_executor=tool_executor,
    llm_client=llm_client,
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


@app.websocket("/ws/dialog/{call_id}")
async def dialog_websocket(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for real-time dialog.

    Accepts JSON messages (gateway protocol):
      - {"type": "call_start", "tenant_id": "...", "session_id": "...", "call_id": "...", "caller_phone": "...", "did": "..."}
      - {"type": "client_speech", "text": "...", "is_final": true, "confidence": 0.95}
      - {"type": "vad_event", "event": "speech_start|speech_end|silence_timeout"}
      - {"type": "interrupt_signal"}
      - {"type": "system_message", "text": "...", "tts_priority": true}

    Accepts JSON messages (legacy protocol):
      - {"type": "process", "tenant_id": "...", "text": "...", "client_phone": "..."}
      - {"type": "reset", "tenant_id": "..."}
      - {"type": "tool_call_result", "tenant_id": "...", "tool_name": "...", "args": {...}, "result": {...}}

    Sends JSON responses:
      - {"type": "ai_response", "text": "..."}
      - {"type": "action", "action": "transfer|hangup", "target": "..."}
      - {"type": "error", "message": "..."}
      - {"type": "response", "data": {...}}  (legacy)
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: call_id={call_id}")

    session_tenant_id: str | None = None
    session_caller_phone: str | None = None

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError as e:
                await websocket.send_json({"type": "error", "message": f"Invalid JSON: {e}"})
                continue

            msg_type = msg.get("type")
            tenant_id = msg.get("tenant_id") or session_tenant_id

            try:
                # --- Gateway protocol handlers ---

                if msg_type == "call_start":
                    session_tenant_id = msg.get("tenant_id")
                    session_caller_phone = msg.get("caller_phone")
                    tenant_id = session_tenant_id
                    if tenant_id:
                        await state_manager.set_context(tenant_id, call_id, "caller_phone", session_caller_phone or "")
                        await state_manager.set_context(tenant_id, call_id, "did", msg.get("did", ""))
                        await state_manager.set_context(tenant_id, call_id, "session_id", msg.get("session_id", ""))
                    logger.info(f"Call started: call_id={call_id}, tenant={tenant_id}")
                    continue

                if msg_type == "system_message":
                    if not tenant_id:
                        await websocket.send_json({"type": "error", "message": "No active session (missing tenant_id)"})
                        continue
                    text = msg.get("text", "")
                    await state_manager.add_message(tenant_id, call_id, "system", text)
                    if msg.get("tts_priority"):
                        await websocket.send_json({"type": "ai_response", "text": text})
                    continue

                if msg_type == "client_speech":
                    if not tenant_id:
                        await websocket.send_json({"type": "error", "message": "No active session (missing tenant_id)"})
                        continue
                    text = msg.get("text", "")
                    is_final = msg.get("is_final", False)
                    if not is_final:
                        continue
                    result = await dialog_manager.process_user_message(
                        tenant_id=tenant_id,
                        call_id=call_id,
                        text=text,
                        client_phone=session_caller_phone,
                    )
                    if result.get("reply"):
                        await websocket.send_json({"type": "ai_response", "text": result["reply"]})
                    for tc in result.get("tool_calls", []):
                        tool_result = tc.get("result", {})
                        if tc.get("tool") == "escalate" or tool_result.get("action") == "transfer":
                            target = tool_result.get("forward_to", "")
                            await websocket.send_json({"type": "action", "action": "transfer", "target": target})
                    continue

                if msg_type == "vad_event":
                    continue

                if msg_type == "interrupt_signal":
                    if tenant_id:
                        await dialog_manager.handle_interrupt(tenant_id, call_id, "")
                    continue

                # --- Legacy protocol handlers ---

                if not tenant_id:
                    await websocket.send_json({"type": "error", "message": "Missing tenant_id"})
                    continue

                if msg_type == "process":
                    result = await dialog_manager.process_user_message(
                        tenant_id=tenant_id,
                        call_id=call_id,
                        text=msg.get("text", ""),
                        client_phone=msg.get("client_phone"),
                    )
                    await websocket.send_json({"type": "response", "data": result})

                elif msg_type == "reset":
                    await state_manager.clear_call(tenant_id, call_id)
                    await websocket.send_json({"type": "response", "data": {"status": "reset"}})

                elif msg_type == "tool_call_result":
                    tool_name = msg.get("tool_name", "")
                    tool_args = msg.get("args", {})
                    tool_result = msg.get("result", {})
                    await state_manager.add_message(
                        tenant_id, call_id,
                        "system",
                        json.dumps({"tool_call": tool_name, "args": tool_args, "result": tool_result}, ensure_ascii=False),
                    )
                    await websocket.send_json({"type": "response", "data": {"status": "stored"}})

                else:
                    await websocket.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})

            except Exception as e:
                logger.exception(f"WebSocket handler error: call_id={call_id}, type={msg_type}")
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: call_id={call_id}")
    except Exception as e:
        logger.exception(f"WebSocket error: call_id={call_id}")
        try:
            await websocket.close()
        except Exception:
            pass


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
