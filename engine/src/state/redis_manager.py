"""Redis session state management for dialog context."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://:allo_redis_pass@redis:6379/0")
SESSION_TTL = 7200  # 2 hours (call duration + 1h buffer)
MAX_HISTORY = 50  # Max messages per dialog


class DialogStateManager:
    """
    Manages dialog context in Redis with tenant isolation.
    Keys: {tenant_id}:call:{call_id}:*
    """

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def init(self):
        """Initialize Redis connection."""
        self.redis = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis connection established")

    async def close(self):
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    def _messages_key(self, tenant_id: str, call_id: str) -> str:
        return f"{tenant_id}:call:{call_id}:messages"

    def _context_key(self, tenant_id: str, call_id: str) -> str:
        return f"{tenant_id}:call:{call_id}:context"

    def _state_key(self, tenant_id: str, call_id: str) -> str:
        return f"{tenant_id}:call:{call_id}:state"

    async def add_message(self, tenant_id: str, call_id: str, role: str, content: str):
        """
        Add a message to the dialog history.
        role: "user" | "assistant" | "system"
        """
        key = self._messages_key(tenant_id, call_id)
        msg = json.dumps({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await self.redis.rpush(key, msg)
        # Trim to max history
        await self.redis.ltrim(key, -MAX_HISTORY, -1)
        await self.redis.expire(key, SESSION_TTL)

    async def get_messages(self, tenant_id: str, call_id: str) -> list[dict]:
        """Get dialog history for a call."""
        key = self._messages_key(tenant_id, call_id)
        raw = await self.redis.lrange(key, 0, -1)
        messages = []
        for r in raw:
            try:
                messages.append(json.loads(r))
            except json.JSONDecodeError:
                continue

        # Filter out system messages for the LLM context
        return messages

    async def get_llm_messages(
        self, tenant_id: str, call_id: str, last_n: int = 20
    ) -> list[dict]:
        """
        Get messages formatted for LLM (role/content pairs).
        Excludes system messages.
        """
        all_msgs = await self.get_messages(tenant_id, call_id)
        llm_msgs = [m for m in all_msgs if m["role"] != "system"]
        return llm_msgs[-last_n:]

    async def set_context(self, tenant_id: str, call_id: str, key: str, value: any):
        """Store a context value for the call."""
        hkey = self._context_key(tenant_id, call_id)
        await self.redis.hset(hkey, key, json.dumps(value))
        await self.redis.expire(hkey, SESSION_TTL)

    async def get_context(self, tenant_id: str, call_id: str, key: str) -> any:
        """Get a context value for the call."""
        hkey = self._context_key(tenant_id, call_id)
        raw = await self.redis.hget(hkey, key)
        if raw:
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return raw
        return None

    async def get_all_context(self, tenant_id: str, call_id: str) -> dict:
        """Get all context for a call."""
        hkey = self._context_key(tenant_id, call_id)
        raw = await self.redis.hgetall(hkey)
        result = {}
        for k, v in raw.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        return result

    async def set_state(self, tenant_id: str, call_id: str, state: str):
        """Set call state (e.g., 'greeting', 'collecting_info', 'booking', 'completed')."""
        key = self._state_key(tenant_id, call_id)
        await self.redis.set(key, state, ex=SESSION_TTL)

    async def get_state(self, tenant_id: str, call_id: str) -> Optional[str]:
        """Get current call state."""
        key = self._state_key(tenant_id, call_id)
        return await self.redis.get(key)

    async def clear_call(self, tenant_id: str, call_id: str):
        """Remove all data for a call."""
        keys = [
            self._messages_key(tenant_id, call_id),
            self._context_key(tenant_id, call_id),
            self._state_key(tenant_id, call_id),
        ]
        await self.redis.delete(*keys)

    async def get_history_for_client(
        self, tenant_id: str, client_phone: str, limit: int = 5
    ) -> list[dict]:
        """
        Get booking history for a client (from Redis cache, fallback to DB).
        This stores recent interactions for quick access.
        """
        key = f"{tenant_id}:client:{client_phone}:recent_bookings"
        raw = await self.redis.lrange(key, 0, limit - 1)
        result = []
        for r in raw:
            try:
                result.append(json.loads(r))
            except json.JSONDecodeError:
                continue
        return result

    async def cache_client_bookings(self, tenant_id: str, client_phone: str, bookings: list[dict]):
        """Cache recent bookings for quick access."""
        key = f"{tenant_id}:client:{client_phone}:recent_bookings"
        await self.redis.delete(key)
        for b in reversed(bookings):
            await self.redis.lpush(key, json.dumps(b))
        await self.redis.expire(key, 3600)  # 1 hour cache
