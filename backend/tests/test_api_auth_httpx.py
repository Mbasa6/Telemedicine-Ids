import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_login_invalid_credentials_httpx():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/auth/login", data={"username": "nouser", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint_httpx():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root_endpoint_httpx():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/")
    assert resp.status_code == 200
    assert "service" in resp.json()
