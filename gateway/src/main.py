"""Voice Gateway — Sipuni SIP integration, call management, and audio relay."""

import asyncio
import hashlib
import hmac
import json
import os
import time
from contextlib import asynccontextmanager
from enum import Enum
from typing import Optional
from uuid import uuid4

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from shared.utils import normalize_phone, retry_async, setup_logging

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SIPUNI_API_KEY = os.getenv("SIPUNI_API_KEY", "")
SIPUNI_ACCOUNT = os.getenv("SIPUNI_ACCOUNT", "")
SIPUNI_SECRET = os.getenv("SIPUNI_SECRET", "")
SIPUNI_API_BASE = os.getenv("SIPUNI_API_BASE", "https://sipuni.com/api")
BOOKING_API_URL = os.getenv("BOOKING_API_URL", "http://booking:8003/api/v1")
SPEECH_WS_URL = os.getenv("SPEECH_WS_URL", "ws://speech:8001")
ENGINE_WS_URL = os.getenv("ENGINE_WS_URL", "ws://engine:8002/ws/dialog")
ALLO_FALLBACK_DIRECT = os.getenv("ALLO_FALLBACK_DIRECT", "")
GATEWAY_DEBUG = os.getenv("GATEWAY_DEBUG", "false").lower() == "true"

logger = setup_logging("gateway", level="DEBUG" if GATEWAY_DEBUG else "INFO")

CONSENT_TEXT_152FZ = (
    "Добро пожаловать! Данный звонок обрабатывается с помощью искусственного "
    "интеллекта. Продолжая разговор, вы соглашаетесь на обработку персональных "
    "данных в соответствии с Федеральным законом №152-ФЗ. Чем могу помочь?"
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CallState(str, Enum):
    RINGING = "ringing"
    SPEAKING = "speaking"
    LISTENING = "listening"
    ESCALATED = "escalated"
    COMPLETED = "completed"


class ActiveCall(BaseModel):
    call_id: str
    session_id: str
    tenant_id: Optional[str] = None
    caller_phone: str
    did: str
    state: CallState = CallState.RINGING
    started_at: float
    consent_played: bool = False


class InboundCallEvent(BaseModel):
    call_id: str
    caller_number: str
    called_number: str
    sip_username: Optional[str] = None
    timestamp: Optional[str] = None
    event_type: str = "incoming"


class TransferRequest(BaseModel):
    target_number: str


# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

active_calls: dict[str, ActiveCall] = {}
call_stats: dict[str, int] = {
    "total_inbound": 0,
    "active": 0,
    "transferred": 0,
    "failed": 0,
}
_http_client: Optional[httpx.AsyncClient] = None


def _mask_phone(phone: str) -> str:
    return phone[:4] + "****" if len(phone) > 4 else "****"


# ---------------------------------------------------------------------------
# HTTP client lifecycle
# ---------------------------------------------------------------------------


async def _get_http() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    return _http_client


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _http_client
    _http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    logger.info("gateway started")
    yield
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
    logger.info("gateway stopped")


app = FastAPI(title="Алло — Voice Gateway", version="1.0.0", lifespan=lifespan)

# ---------------------------------------------------------------------------
# HMAC-SHA256 signature verification
# ---------------------------------------------------------------------------


def _verify_signature(body: bytes, signature: str) -> bool:
    if not SIPUNI_SECRET:
        logger.warning("SIPUNI_SECRET not set — signature check skipped")
        return True
    expected = hmac.new(SIPUNI_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# DID -> tenant routing
# ---------------------------------------------------------------------------


async def _resolve_tenant(did: str, sip_username: Optional[str] = None) -> Optional[dict]:
    client = await _get_http()
    try:
        params: dict[str, str] = {"did": normalize_phone(did)}
        if sip_username:
            params["sip_username"] = sip_username
        resp = await client.get(f"{BOOKING_API_URL}/sip/resolve", params=params)
        if resp.status_code == 200:
            return resp.json()
        logger.warning("tenant not found for did=%s status=%d", _mask_phone(did), resp.status_code)
    except Exception:
        logger.exception("tenant resolution error")
    return None


# ---------------------------------------------------------------------------
# Sipuni API helpers
# ---------------------------------------------------------------------------


async def _sipuni_call(method: str, endpoint: str, **kwargs) -> Optional[httpx.Response]:
    client = await _get_http()
    url = f"{SIPUNI_API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {SIPUNI_API_KEY}",
        "X-Account": SIPUNI_ACCOUNT,
    }

    async def _request():
        resp = await client.request(method, url, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    try:
        result = await retry_async(_request, max_retries=3, delay=0.5, backoff=2.0)
        logger.info("sipuni %s /%s -> %d", method, endpoint, result.status_code)
        return result
    except Exception:
        logger.exception("sipuni call failed: %s /%s", method, endpoint)
        call_stats["failed"] += 1
        return None


async def _forward_to_owner(caller_phone: str, did: str) -> None:
    if not ALLO_FALLBACK_DIRECT:
        logger.error("ALLO_FALLBACK_DIRECT not set — cannot forward")
        return
    logger.info(
        "forwarding to owner: caller=%s did=%s",
        _mask_phone(caller_phone),
        _mask_phone(did),
    )
    await _sipuni_call(
        "POST",
        "call/transfer",
        json={"from": did, "to": ALLO_FALLBACK_DIRECT, "caller": caller_phone},
    )


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "gateway",
        "active_calls": len(active_calls),
        "stats": call_stats,
        "sipuni_configured": bool(SIPUNI_API_KEY),
    }


@app.post("/api/v1/calls/inbound")
async def inbound_call(
    request: Request,
    x_sipuni_signature: Optional[str] = Header(None),
):
    body = await request.body()

    if not _verify_signature(body, x_sipuni_signature or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event = InboundCallEvent(**json.loads(body))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    call_stats["total_inbound"] += 1

    tenant = await _resolve_tenant(event.called_number, event.sip_username)
    tenant_id = tenant.get("tenant_id") if tenant else None

    if not tenant_id:
        logger.warning("no tenant for did=%s — forwarding", _mask_phone(event.called_number))
        await _forward_to_owner(event.caller_number, event.called_number)
        return {"status": "forwarded", "reason": "tenant_not_found"}

    session_id = str(uuid4())
    call = ActiveCall(
        call_id=event.call_id,
        session_id=session_id,
        tenant_id=tenant_id,
        caller_phone=normalize_phone(event.caller_number),
        did=event.called_number,
        started_at=time.time(),
    )
    active_calls[event.call_id] = call
    call_stats["active"] = len(active_calls)

    logger.info(
        "inbound call_id=%s session=%s tenant=%s", event.call_id, session_id, tenant_id
    )
    return {
        "status": "accepted",
        "session_id": session_id,
        "call_id": event.call_id,
        "tenant_id": tenant_id,
        "consent_text": CONSENT_TEXT_152FZ,
    }


@app.post("/api/v1/calls/{call_id}/transfer")
async def transfer_call(call_id: str, req: TransferRequest):
    call = active_calls.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    resp = await _sipuni_call(
        "POST",
        "call/transfer",
        json={"call_id": call_id, "target": req.target_number, "account": SIPUNI_ACCOUNT},
    )
    if not resp:
        raise HTTPException(status_code=502, detail="Transfer failed")

    call.state = CallState.ESCALATED
    call_stats["transferred"] += 1
    logger.info("transferred call_id=%s", call_id)
    return {"status": "transferred", "call_id": call_id}


@app.post("/api/v1/calls/{call_id}/hangup")
async def hangup_call(call_id: str):
    call = active_calls.pop(call_id, None)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    await _sipuni_call(
        "POST",
        "call/hangup",
        json={"call_id": call_id, "account": SIPUNI_ACCOUNT},
    )

    duration = int(time.time() - call.started_at)
    call_stats["active"] = len(active_calls)
    logger.info("hangup call_id=%s duration=%ds", call_id, duration)
    return {"status": "completed", "call_id": call_id, "duration_sec": duration}


# ---------------------------------------------------------------------------
# WebSocket audio relay
# ---------------------------------------------------------------------------


@app.websocket("/ws/audio/{session_id}")
async def audio_relay(ws: WebSocket, session_id: str):
    await ws.accept()

    call = next((c for c in active_calls.values() if c.session_id == session_id), None)
    if not call:
        await ws.close(code=4004, reason="Session not found")
        return

    call.state = CallState.LISTENING
    import websockets

    asr_url = f"{SPEECH_WS_URL}/ws/asr"
    vad_url = f"{SPEECH_WS_URL}/ws/vad"
    engine_url = f"{ENGINE_WS_URL}/{session_id}"
    tts_url = f"{SPEECH_WS_URL}/ws/tts"

    asr_ws = None
    vad_ws = None
    engine_ws = None

    try:
        asr_ws, vad_ws, engine_ws = await asyncio.gather(
            websockets.connect(asr_url),
            websockets.connect(vad_url),
            websockets.connect(engine_url),
        )

        await engine_ws.send(json.dumps({
            "type": "call_start",
            "session_id": session_id,
            "call_id": call.call_id,
            "tenant_id": call.tenant_id,
            "caller_phone": call.caller_phone,
            "did": call.did,
        }))

        if not call.consent_played:
            await engine_ws.send(json.dumps({
                "type": "system_message",
                "text": CONSENT_TEXT_152FZ,
                "tts_priority": True,
            }))
            call.consent_played = True
            call.state = CallState.SPEAKING

        stop = asyncio.Event()

        async def _client_to_speech():
            try:
                while not stop.is_set():
                    data = await ws.receive_bytes()
                    await asyncio.gather(
                        asr_ws.send(data),
                        vad_ws.send(data),
                    )
            except WebSocketDisconnect:
                stop.set()
            except Exception:
                logger.exception("client->speech error session=%s", session_id)
                stop.set()

        async def _asr_to_engine():
            try:
                async for msg in asr_ws:
                    if stop.is_set():
                        break
                    transcript = json.loads(msg) if isinstance(msg, str) else json.loads(msg.decode())
                    await engine_ws.send(json.dumps({
                        "type": "client_speech",
                        "text": transcript.get("text", ""),
                        "is_final": transcript.get("is_final", False),
                        "confidence": transcript.get("confidence"),
                    }))
                    if transcript.get("is_final"):
                        call.state = CallState.SPEAKING
            except Exception:
                logger.exception("asr->engine error session=%s", session_id)
                stop.set()

        async def _vad_to_engine():
            try:
                async for msg in vad_ws:
                    if stop.is_set():
                        break
                    event = json.loads(msg) if isinstance(msg, str) else json.loads(msg.decode())
                    event_type = event.get("event")
                    if event_type in ("speech_start", "speech_end", "silence_timeout"):
                        await engine_ws.send(json.dumps({
                            "type": "vad_event",
                            "event": event_type,
                        }))
                        if event_type == "speech_start" and call.state == CallState.SPEAKING:
                            await engine_ws.send(json.dumps({"type": "interrupt_signal"}))
            except Exception:
                logger.exception("vad->engine error session=%s", session_id)
                stop.set()

        async def _engine_to_client():
            try:
                async for msg in engine_ws:
                    if stop.is_set():
                        break
                    response = json.loads(msg) if isinstance(msg, str) else json.loads(msg.decode())
                    rtype = response.get("type", "")

                    if rtype == "ai_response":
                        call.state = CallState.SPEAKING
                        try:
                            async with websockets.connect(tts_url) as tts_ws:
                                await tts_ws.send(json.dumps({
                                    "text": response["text"],
                                    "voice": "alena",
                                }))
                                async for chunk in tts_ws:
                                    if isinstance(chunk, bytes):
                                        await ws.send_bytes(chunk)
                        except Exception:
                            logger.exception("tts relay error session=%s", session_id)
                        call.state = CallState.LISTENING

                    elif rtype == "action":
                        action = response.get("action", "")
                        if action == "transfer":
                            target = response.get("target", ALLO_FALLBACK_DIRECT)
                            await _sipuni_call(
                                "POST", "call/transfer",
                                json={"call_id": call.call_id, "target": target},
                            )
                            call.state = CallState.ESCALATED
                            stop.set()
                        elif action == "hangup":
                            stop.set()

                    elif rtype == "error":
                        logger.error("engine error session=%s: %s", session_id, response.get("message"))
                        await _forward_to_owner(call.caller_phone, call.did)
                        stop.set()
            except Exception:
                logger.exception("engine->client error session=%s", session_id)
                stop.set()

        await asyncio.gather(
            _client_to_speech(),
            _asr_to_engine(),
            _vad_to_engine(),
            _engine_to_client(),
        )

    except Exception:
        logger.exception("audio relay setup failed session=%s", session_id)
        await _forward_to_owner(call.caller_phone, call.did)

    finally:
        for conn in (asr_ws, vad_ws, engine_ws):
            if conn:
                try:
                    await conn.close()
                except Exception:
                    pass
        active_calls.pop(call.call_id, None)
        call_stats["active"] = len(active_calls)
        try:
            await ws.close()
        except Exception:
            pass
        logger.info("relay ended session=%s", session_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
