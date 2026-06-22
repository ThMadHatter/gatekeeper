import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_help_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/help/")
    assert response.status_code == 200
    assert "endpoints" in response.json()

@pytest.mark.asyncio
async def test_list_repos_endpoint():
    with patch("app.routers.repos.RepoService.list_repos", return_value=[]):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/repos/")
        assert response.status_code == 200
        assert response.json()["data"] == []

@pytest.mark.asyncio
async def test_add_repo_endpoint_success():
    with patch("app.routers.repos.RepoService.add_repo", return_value={"name": "test", "url": "url"}):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/repos/", json={"name": "test", "url": "url"})
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "test"

@pytest.mark.asyncio
async def test_add_repo_endpoint_error():
    with patch("app.routers.repos.RepoService.add_repo", side_effect=Exception("Error")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/repos/", json={"name": "test", "url": "url"})
        assert response.status_code == 400
        assert "Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_remove_repo_endpoint_success():
    with patch("app.routers.repos.RepoService.remove_repo"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.delete("/repos/test")
        assert response.status_code == 200
        assert "removed" in response.json()["message"]

@pytest.mark.asyncio
async def test_remove_repo_endpoint_error():
    with patch("app.routers.repos.RepoService.remove_repo", side_effect=Exception("Missing")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.delete("/repos/test")
        assert response.status_code == 404
        assert "Missing" in response.json()["detail"]
