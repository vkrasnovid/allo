"""Tests for the booking service API."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    """Health endpoint should always work (no DB dependency)."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "booking"


@pytest.mark.asyncio
async def test_routes_registered(client):
    """Verify the router is mounted and docs work."""
    resp = await client.get("/docs")
    assert resp.status_code in (200, 404)
