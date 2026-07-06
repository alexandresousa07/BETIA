import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_ai_models(client):
    response = await client.get("/api/v1/ai/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 8


@pytest.mark.asyncio
async def test_list_markets(client):
    response = await client.get("/api/v1/ai/markets")
    assert response.status_code == 200
    data = response.json()
    assert any(m["key"] == "over_2.5_goals" for m in data["data"])
