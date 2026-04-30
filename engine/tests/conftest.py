"""Shared test fixtures and configuration."""

import socket

import pytest


def redis_available() -> bool:
    """Check if Redis is available by trying to connect."""
    try:
        sock = socket.create_connection(("localhost", 6379), timeout=1)
        sock.close()
        return True
    except (OSError, socket.gaierror):
        pass
    try:
        sock = socket.create_connection(("redis", 6379), timeout=1)
        sock.close()
        return True
    except (OSError, socket.gaierror):
        return False


redis_required = pytest.mark.skipif(
    not redis_available(),
    reason="Redis is not available",
)
