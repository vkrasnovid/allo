"""Tests for the engine service HTTP endpoints."""

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
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_compose_prompt(client):
    """Test the prompt building endpoint."""
    resp = await client.post(
        "/api/engine/prompt",
        json={"business_name": "Тестовый салон"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "prompt" in data
    assert "tool_definitions" in data
    assert len(data["prompt"]) > 100
    assert "Тестовый салон" in data["prompt"]


@pytest.mark.asyncio
async def test_stats(client):
    """Test stats endpoint."""
    resp = await client.get("/api/engine/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "hallucination_events" in data
    assert data["service"] == "engine"
