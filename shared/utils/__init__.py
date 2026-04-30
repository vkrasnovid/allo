"""Shared utility functions for the Алло project."""

import logging
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """Configure structured logging for a service."""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    logger.addHandler(handler)
    return logger


async def retry_async(
    fn: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    **kwargs: Any,
) -> T:
    """Retry an async function with exponential backoff."""
    import asyncio

    last_exception: Exception | None = None
    current_delay = delay

    for attempt in range(max_retries):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff

    raise last_exception  # type: ignore


def normalize_phone(phone: str) -> str:
    """Normalize phone number to +7XXXXXXXXXX format."""
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if cleaned.startswith("8"):
        cleaned = "+7" + cleaned[1:]
    elif cleaned.startswith("7"):
        cleaned = "+" + cleaned
    elif not cleaned.startswith("+"):
        cleaned = "+7" + cleaned
    return cleaned
