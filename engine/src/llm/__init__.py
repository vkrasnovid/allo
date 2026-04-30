"""
OpenClaw Integration Client.
HTTP client to communicate with OpenClaw Gateway for LLM inference.
Supports SSE streaming for real-time responses.
"""

import json
from typing import Any, AsyncGenerator, Optional

import httpx


class LLMChunk:
    """A chunk from the LLM stream."""

    def __init__(self, event: str, data: dict):
        self.event = event
        self.data = data


class OpenClawLLMClient:
    """HTTP client to OpenClaw Gateway — sends prompts + tools, receives streaming responses."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0, headers=self.headers)

    async def chat_stream(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> AsyncGenerator[LLMChunk, None]:
        """Streaming chat completion through OpenClaw Gateway. Yields LLMChunk events."""
        payload = {
            "model": "deepseek/deepseek-v4-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        async with self.client.stream("POST", f"{self.base_url}/api/llm/chat", json=payload) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                raise RuntimeError(f"LLM request failed ({response.status_code}): {error_body.decode()}")

            current_event = "message"
            async for line in response.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("event: "):
                    current_event = line[7:].strip()
                elif line.startswith("data: "):
                    data = json.loads(line[6:])
                    yield LLMChunk(event=current_event, data=data)

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> dict:
        """Non-streaming chat completion."""
        payload = {
            "model": "deepseek/deepseek-v4-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        resp = await self.client.post(f"{self.base_url}/api/llm/chat", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
