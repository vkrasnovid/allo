"""Speech Services — Yandex SpeechKit ASR/TTS and energy-based VAD."""

import asyncio
import json
import math
import os
import struct
import time
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from shared.utils import retry_async, setup_logging

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

YC_API_KEY = os.getenv("YC_API_KEY", "")
ASR_LANG = os.getenv("ASR_LANG", "ru-RU")
TTS_VOICE = os.getenv("TTS_VOICE", "alena")
SPEECH_DEBUG = os.getenv("SPEECH_DEBUG", "false").lower() == "true"

YANDEX_STT_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
YANDEX_TTS_URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

SAMPLE_RATE = 8000
FRAME_DURATION_MS = 20
FRAME_SIZE = SAMPLE_RATE * FRAME_DURATION_MS // 1000  # 160 samples
FRAME_BYTES = FRAME_SIZE * 2  # 320 bytes per frame (PCM16)

VAD_RMS_THRESHOLD = 300.0
VAD_MIN_SPEECH_FRAMES = 15   # 300ms
VAD_MIN_SILENCE_FRAMES = 40  # 800ms
VAD_SILENCE_TIMEOUT_FRAMES = 150  # 3000ms

ASR_CHUNK_SECONDS = 2
ASR_CHUNK_BYTES = SAMPLE_RATE * 2 * ASR_CHUNK_SECONDS  # 32000 bytes

BEAUTY_SALON_HINTS = [
    "стрижка", "окрашивание", "маникюр", "педикюр", "укладка",
    "мелирование", "балаяж", "шатуш", "кератин", "ботокс",
    "ламинирование", "наращивание", "эпиляция", "депиляция",
    "чистка лица", "пилинг", "массаж", "записаться", "запись",
    "свободно", "салон", "услуга", "цена", "стоимость", "мастер",
    "парикмахер", "косметолог", "бровист", "лашмейкер", "ногти",
    "гель-лак", "шеллак", "брови", "ресницы", "тонирование",
]

logger = setup_logging("speech", level="DEBUG" if SPEECH_DEBUG else "INFO")

# ---------------------------------------------------------------------------
# HTTP client lifecycle
# ---------------------------------------------------------------------------

_http_client: Optional[httpx.AsyncClient] = None


async def _get_http() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    return _http_client


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _http_client
    _http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    logger.info("speech service started")
    yield
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
    logger.info("speech service stopped")


app = FastAPI(title="Алло — Speech Services", version="1.0.0", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Yandex SpeechKit API helpers
# ---------------------------------------------------------------------------


def _yc_headers() -> dict[str, str]:
    return {"Authorization": f"Api-Key {YC_API_KEY}"}


async def _recognize_audio(audio: bytes, lang: str = ASR_LANG) -> dict:
    client = await _get_http()

    async def _call():
        resp = await client.post(
            YANDEX_STT_URL,
            headers=_yc_headers(),
            params={
                "lang": lang,
                "topic": "general",
                "format": "lpcm",
                "sampleRateHertz": str(SAMPLE_RATE),
            },
            content=audio,
        )
        resp.raise_for_status()
        return resp.json()

    return await retry_async(_call, max_retries=3, delay=0.3, backoff=2.0)


async def _synthesize_speech(
    text: str, voice: str = TTS_VOICE, lang: str = ASR_LANG
) -> bytes:
    client = await _get_http()

    async def _call():
        resp = await client.post(
            YANDEX_TTS_URL,
            headers=_yc_headers(),
            data={
                "text": text,
                "lang": lang,
                "voice": voice,
                "format": "lpcm",
                "sampleRateHertz": str(SAMPLE_RATE),
            },
        )
        resp.raise_for_status()
        return resp.content

    return await retry_async(_call, max_retries=3, delay=0.3, backoff=2.0)


# ---------------------------------------------------------------------------
# VAD helpers
# ---------------------------------------------------------------------------


def _rms(frame: bytes) -> float:
    n_samples = len(frame) // 2
    if n_samples == 0:
        return 0.0
    samples = struct.unpack(f"<{n_samples}h", frame[: n_samples * 2])
    return math.sqrt(sum(s * s for s in samples) / n_samples)


def _speech_probability(rms_val: float, threshold: float = VAD_RMS_THRESHOLD) -> float:
    if rms_val <= 0:
        return 0.0
    ratio = rms_val / threshold
    return min(1.0, ratio * ratio / (1.0 + ratio * ratio))


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "speech",
        "yc_api_key_set": bool(YC_API_KEY),
        "asr_lang": ASR_LANG,
        "tts_voice": TTS_VOICE,
    }


# ---------------------------------------------------------------------------
# WS /ws/asr — Streaming ASR
# ---------------------------------------------------------------------------


@app.websocket("/ws/asr")
async def ws_asr(ws: WebSocket):
    await ws.accept()
    logger.info("asr session started")

    audio_buffer = bytearray()
    total_bytes = 0
    utterance_id = 0

    try:
        while True:
            data = await ws.receive()

            if "bytes" in data and data["bytes"]:
                chunk = data["bytes"]
                audio_buffer.extend(chunk)
                total_bytes += len(chunk)

                if len(audio_buffer) >= ASR_CHUNK_BYTES:
                    segment = bytes(audio_buffer)
                    audio_buffer.clear()
                    try:
                        result = await _recognize_audio(segment)
                        text = result.get("result", "")
                        if text:
                            await ws.send_json({
                                "text": text,
                                "is_final": False,
                                "confidence": None,
                                "utterance_id": utterance_id,
                            })
                            logger.info("asr partial len=%d", len(text))
                    except Exception:
                        logger.exception("asr recognition error")

            elif "text" in data and data["text"]:
                msg = json.loads(data["text"])
                cmd = msg.get("type", "")

                if cmd == "end_utterance":
                    if audio_buffer:
                        segment = bytes(audio_buffer)
                        audio_buffer.clear()
                        try:
                            result = await _recognize_audio(segment)
                            text = result.get("result", "")
                            await ws.send_json({
                                "text": text,
                                "is_final": True,
                                "confidence": result.get("confidence"),
                                "utterance_id": utterance_id,
                            })
                            logger.info("asr final len=%d", len(text))
                        except Exception:
                            logger.exception("asr final recognition error")
                            await ws.send_json({
                                "text": "",
                                "is_final": True,
                                "confidence": None,
                                "utterance_id": utterance_id,
                                "error": "recognition_failed",
                            })
                    else:
                        await ws.send_json({
                            "text": "",
                            "is_final": True,
                            "confidence": None,
                            "utterance_id": utterance_id,
                        })
                    utterance_id += 1

                elif cmd == "config":
                    logger.info("asr config received: %s", {
                        k: v for k, v in msg.items() if k != "type"
                    })

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("asr session error")
    finally:
        if audio_buffer:
            try:
                result = await _recognize_audio(bytes(audio_buffer))
                text = result.get("result", "")
                if text:
                    await ws.send_json({
                        "text": text,
                        "is_final": True,
                        "confidence": result.get("confidence"),
                        "utterance_id": utterance_id,
                    })
            except Exception:
                pass
        try:
            await ws.close()
        except Exception:
            pass
        logger.info("asr session ended total_bytes=%d", total_bytes)


# ---------------------------------------------------------------------------
# WS /ws/tts — Streaming TTS
# ---------------------------------------------------------------------------

TTS_CHUNK_SIZE = 4096


@app.websocket("/ws/tts")
async def ws_tts(ws: WebSocket):
    await ws.accept()
    logger.info("tts session started")

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            text = msg.get("text", "")
            voice = msg.get("voice", TTS_VOICE)

            if not text:
                await ws.send_json({"error": "empty_text"})
                continue

            logger.info("tts request voice=%s text_len=%d", voice, len(text))

            try:
                audio = await _synthesize_speech(text, voice=voice)
                offset = 0
                seq = 0
                while offset < len(audio):
                    end = min(offset + TTS_CHUNK_SIZE, len(audio))
                    await ws.send_bytes(audio[offset:end])
                    seq += 1
                    offset = end
                await ws.send_json({"type": "done", "chunks": seq, "bytes": len(audio)})
                logger.info("tts done chunks=%d bytes=%d", seq, len(audio))
            except Exception:
                logger.exception("tts synthesis error")
                await ws.send_json({"type": "error", "message": "synthesis_failed"})

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("tts session error")
    finally:
        try:
            await ws.close()
        except Exception:
            pass
        logger.info("tts session ended")


# ---------------------------------------------------------------------------
# WS /ws/vad — Voice Activity Detection
# ---------------------------------------------------------------------------


@app.websocket("/ws/vad")
async def ws_vad(ws: WebSocket):
    await ws.accept()
    logger.info("vad session started")

    in_speech = False
    speech_frames = 0
    silence_frames = 0
    total_frames = 0

    try:
        while True:
            data = await ws.receive_bytes()

            offset = 0
            while offset + FRAME_BYTES <= len(data):
                frame = data[offset : offset + FRAME_BYTES]
                offset += FRAME_BYTES
                total_frames += 1

                rms_val = _rms(frame)
                prob = _speech_probability(rms_val)
                is_speech_frame = rms_val > VAD_RMS_THRESHOLD

                if is_speech_frame:
                    speech_frames += 1
                    silence_frames = 0

                    if not in_speech and speech_frames >= VAD_MIN_SPEECH_FRAMES:
                        in_speech = True
                        await ws.send_json({
                            "event": "speech_start",
                            "is_speech": True,
                            "probability": round(prob, 3),
                            "frame": total_frames,
                        })
                        logger.debug("vad speech_start frame=%d", total_frames)
                else:
                    silence_frames += 1
                    if in_speech:
                        speech_frames = 0
                        if silence_frames >= VAD_MIN_SILENCE_FRAMES:
                            in_speech = False
                            await ws.send_json({
                                "event": "speech_end",
                                "is_speech": False,
                                "probability": round(prob, 3),
                                "frame": total_frames,
                            })
                            logger.debug("vad speech_end frame=%d", total_frames)
                    else:
                        speech_frames = 0
                        if silence_frames >= VAD_SILENCE_TIMEOUT_FRAMES:
                            await ws.send_json({
                                "event": "silence_timeout",
                                "is_speech": False,
                                "probability": 0.0,
                                "frame": total_frames,
                            })
                            silence_frames = 0
                            logger.debug("vad silence_timeout frame=%d", total_frames)

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("vad session error")
    finally:
        try:
            await ws.close()
        except Exception:
            pass
        logger.info("vad session ended total_frames=%d", total_frames)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
